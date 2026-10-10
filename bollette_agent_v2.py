"""
Bollette agent v2: every decision is a typed Jev question instead of an LLM prompt.

Per user message the agent makes at most two Decisions API calls:
  1. intent + which slip bet + which match (+ does that match exist), asked in parallel
  2. which sign, asked only about the selected match (so "Inter lose" can be resolved
     against the real home/away teams)

Jev returns probabilities, not text, so user-facing messages are templates. The bet amount
is a Choice over common stakes asked in call 1; OpenAI is the fallback when the stake is
not in that set.
"""
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from logger_config import setup_logger
from third_parties.jev import MAX_CHOICE_OPTIONS, decide

logger = setup_logger(__name__)

PAYSLIPS_V2: Dict[str, List[Dict[str, Any]]] = {}

# Starting points, not tuned values: pick them from labeled prompts once we have some.
MATCH_EXISTS_MIN = 0.5
SLIP_EXISTS_MIN = 0.5
SIGN_MIN_PROBABILITY = 0.4
AMOUNT_MIN_PROBABILITY = 0.6

INTENTS = {
    "add": "The user wants to add a bet on a match to the slip, e.g. 'Roma over', 'Juve X', "
           "'I want Manchester United to win'.",
    "remove": "The user wants to take a bet that is already in the slip out of it.",
    "replace": "The user wants to swap a bet already in the slip with a different bet.",
    "checkout": "The user confirms the slip or says how much to bet, e.g. 'ok', 'checkout 20', "
                "'bet 10 euros'.",
    "other": "Anything else: greetings, questions, text unrelated to the bet slip.",
}

SIGNS = {
    "home": "The home team (listed first) wins. Also written '1', or 'the away team loses'.",
    "draw": "The match ends in a draw. Also written 'X'.",
    "away": "The away team (listed second) wins. Also written '2', or 'the home team loses'.",
    "over": "More than 2.5 total goals, e.g. 'over', 'over 2.5'.",
    "under": "Fewer than 2.5 total goals, e.g. 'under', 'under 2.5'.",
    "gg": "Both teams score, e.g. 'GG', 'goal', 'both teams to score'.",
    "ng": "At least one team does not score, e.g. 'NG', 'no goal'.",
}
UNSPECIFIED_SIGN = "unspecified"

# Stakes people actually type; anything else ("7,33") goes to the OpenAI fallback.
COMMON_AMOUNTS = sorted(
    {0.5, 1.5, 2.5}
    | set(range(1, 31))
    | set(range(35, 101, 5))
    | set(range(110, 301, 10))
    | set(range(350, 1001, 50))
    | set(range(1500, 5001, 500))
)
NO_AMOUNT = "none"
OTHER_AMOUNT = "other"

NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")


def get_matches() -> List[Dict[str, Any]]:
    # Imported lazily: tools.match_list starts fetching tournament data on import.
    from tools import match_list
    return match_list.tournaments_data


def match_line_id(i: int) -> str:
    return f"M{i:04d}"


def slip_line_id(i: int) -> str:
    return f"P{i:02d}"


def describe_match(match: Dict[str, Any]) -> str:
    teams = match.get("teams") or []
    parts = [f"{teams[0]} - {teams[1]}"]
    if match.get("sport_key"):
        parts.append(str(match["sport_key"]))
    if match.get("start"):
        parts.append(str(match["start"]))
    return ", ".join(parts)


def describe_bet(bet: Dict[str, Any]) -> str:
    teams = bet.get("teams") or []
    return f"{' - '.join(teams)}, sign: {bet.get('sign')}"


def startup(user_input: str) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    PAYSLIPS_V2[session_id] = []
    res = process_action(session_id, user_input)
    return {"id": session_id, **res}


def build_main_questions(matches: List[Dict[str, Any]], payslip: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    questions: Dict[str, Dict[str, Any]] = {
        "intent": {
            "type": "choice",
            "instructions": "What does the user want to do with their bet slip?",
            "criteria": INTENTS,
        },
        "amount": {
            "type": "choice",
            "instructions": "How much money does the user want to bet on the slip?",
            "criteria": {
                **{amount_key(a): None for a in COMMON_AMOUNTS},
                NO_AMOUNT: "The user does not say how much to bet.",
                OTHER_AMOUNT: "The user says an amount that is not exactly one of the listed numbers.",
            },
        },
    }

    if payslip:
        questions["slip_target"] = {
            "type": "choice",
            "instructions": "If the user wants to remove or replace a bet, which line of bet_slip is it? "
                            "For a replace, pick the bet being taken out.",
            "criteria": {slip_line_id(i): None for i in range(len(payslip))},
        }
        questions["slip_mentioned"] = {
            "type": "noul",
            "instructions": "Does the user refer to a bet that is in bet_slip?",
            "criteria": {
                "true": "The user names a team or match that appears in bet_slip.",
                "false": "No bet in bet_slip matches what the user refers to.",
            },
        }

    if matches:
        questions["match_mentioned"] = {
            "type": "noul",
            "instructions": "Does the user refer to a match listed in available_matches?",
            "criteria": {
                "true": "The user names a team or match that appears in available_matches.",
                "false": "No match in available_matches fits what the user refers to.",
            },
        }
        # Split into chunks because a Choice question accepts at most 255 options.
        for chunk, start in enumerate(range(0, len(matches), MAX_CHOICE_OPTIONS)):
            end = min(start + MAX_CHOICE_OPTIONS, len(matches))
            questions[f"match_{chunk}"] = {
                "type": "choice",
                "instructions": "Which line of available_matches is the match the user wants to bet on? "
                                "For a replace, pick the new match being added. "
                                f"Only lines {match_line_id(start)} to {match_line_id(end - 1)} are options.",
                "criteria": {match_line_id(i): None for i in range(start, end)},
            }

    return questions


def pick_match(answers: Dict[str, Any], matches: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], float]:
    """Return the selected match and its probability, choosing the most peaked chunk when there are several."""
    best_id, best_probability = None, -1.0
    for key, answer in answers.items():
        if not key.startswith("match_") or key == "match_mentioned":
            continue
        choice = answer.get("choice")
        probability = (answer.get("probabilities") or {}).get(choice, 0.0)
        if probability > best_probability:
            best_id, best_probability = choice, probability
    if not best_id:
        return None, 0.0
    index = int(best_id[1:])
    return (matches[index] if index < len(matches) else None), best_probability


def resolve_sign(user_input: str, match: Dict[str, Any], session_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
    odds = match.get("odds") or {}
    criteria = {sign: description for sign, description in SIGNS.items() if odds.get(sign)}
    criteria[UNSPECIFIED_SIGN] = "The user does not say which outcome they want to bet on."
    teams = match.get("teams") or []
    state = {
        "user_message": user_input,
        "match": {"home_team": teams[0], "away_team": teams[1]},
    }
    questions = {
        "sign": {
            "type": "choice",
            "instructions": "Which outcome of this match does the user want to bet on?",
            "criteria": criteria,
        }
    }
    answer = decide(state, questions, session_id=session_id)["answers"]["sign"]
    sign = answer.get("choice")
    probability = (answer.get("probabilities") or {}).get(sign, 0.0)
    if sign == UNSPECIFIED_SIGN or probability < SIGN_MIN_PROBABILITY:
        return None, answer
    return sign, answer


def add_to_payslip(payslip: List[Dict[str, Any]], match: Dict[str, Any], sign: str) -> List[Dict[str, Any]]:
    bet = {
        "id": match.get("id"),
        "sport_key": match.get("sport_key"),
        "matchId": match.get("matchId"),
        "teams": match.get("teams"),
        "start": match.get("start"),
        "odd": (match.get("odds") or {}).get(sign),
        "sign": sign,
    }
    for i, existing in enumerate(payslip):
        if existing.get("id") == bet["id"]:
            payslip[i] = bet
            return payslip
    payslip.append(bet)
    return payslip


def amount_key(amount: float) -> str:
    return f"{amount:g}"


def numbers_in(user_input: str) -> List[float]:
    return [float(n.replace(",", ".")) for n in NUMBER_PATTERN.findall(user_input)]


def openai_amount(user_input: str) -> Optional[float]:
    # Imported lazily: only needed when Jev can't place the amount in COMMON_AMOUNTS.
    from agents.bet_amount_retrieval import get_bet_amount
    try:
        amount = get_bet_amount(user_input).amount
    except Exception as e:
        logger.error(f"OpenAI amount fallback failed: {e}")
        return None
    return amount if amount and amount > 0 else None


def resolve_amount(user_input: str, answer: Dict[str, Any]) -> Tuple[Optional[float], str]:
    """Return the bet amount and where it came from: 'jev', 'openai' or 'none'."""
    choice = answer.get("choice")
    probability = (answer.get("probabilities") or {}).get(choice, 0.0)
    numbers = numbers_in(user_input)

    if choice == NO_AMOUNT and probability >= AMOUNT_MIN_PROBABILITY and not numbers:
        return None, "none"
    if choice not in (NO_AMOUNT, OTHER_AMOUNT) and probability >= AMOUNT_MIN_PROBABILITY:
        amount = float(choice)
        # Jev may snap "7,33" to the nearest option: if the user typed digits, they must match.
        if not numbers or amount in numbers:
            return amount, "jev"

    amount = openai_amount(user_input)
    return amount, ("openai" if amount is not None else "none")


def process_action(session_id: str, user_input: str) -> Dict[str, Any]:
    payslip = PAYSLIPS_V2[session_id]
    matches = [m for m in get_matches() if len(m.get("teams") or []) >= 2]

    state = {
        "user_message": user_input,
        "bet_slip": "\n".join(f"{slip_line_id(i)}| {describe_bet(b)}" for i, b in enumerate(payslip)) or "(empty)",
        "available_matches": "\n".join(f"{match_line_id(i)}| {describe_match(m)}" for i, m in enumerate(matches)),
    }
    answers = decide(state, build_main_questions(matches, payslip), session_id=session_id)["answers"]

    intent = answers["intent"].get("choice")
    decision: Dict[str, Any] = {"intent": answers["intent"]}
    logger.info(f"User {session_id} wants to {intent} ({answers['intent'].get('probabilities')})")

    if intent == "checkout":
        if not payslip:
            return {"message": "Your slip is empty, add a bet first.", "payslip": payslip, "decision": decision}
        amount, decision["amount_source"] = resolve_amount(user_input, answers["amount"])
        decision["amount"] = answers["amount"]
        if amount is None:
            return {"message": "How much do you want to bet? For example: 'checkout 10'.",
                    "payslip": payslip, "decision": decision}
        multiplier = 1.0
        for bet in payslip:
            multiplier *= bet.get("odd")
        del PAYSLIPS_V2[session_id]
        return {"message": f"Bet placed: {amount:g} on {len(payslip)} matches.", "amount": amount,
                "max_win": multiplier * amount, "multiplier": multiplier, "decision": decision}

    if intent in ("remove", "replace"):
        decision["slip_mentioned"] = answers.get("slip_mentioned")
        if not payslip or answers["slip_mentioned"]["noul"] < SLIP_EXISTS_MIN:
            return {"message": "I couldn't find that bet in your slip.", "payslip": payslip, "decision": decision}
        slip_index = int(answers["slip_target"]["choice"][1:])
        if intent == "remove":
            removed = payslip.pop(slip_index)
            return {"message": f"Removed {' - '.join(removed.get('teams') or [])} from your slip.",
                    "payslip": payslip, "decision": decision}

    if intent in ("add", "replace"):
        decision["match_mentioned"] = answers.get("match_mentioned")
        match, probability = pick_match(answers, matches)
        decision["match_probability"] = probability
        if not match or answers["match_mentioned"]["noul"] < MATCH_EXISTS_MIN:
            return {"message": "I couldn't find that match among the available ones.", "payslip": payslip,
                    "decision": decision}
        sign, sign_answer = resolve_sign(user_input, match, session_id)
        decision["sign"] = sign_answer
        teams = " - ".join(match.get("teams") or [])
        if not sign:
            return {"message": f"Which result do you want for {teams}? (1, X, 2, over, under, GG, NG)",
                    "payslip": payslip, "decision": decision}
        if intent == "replace":
            # Only drop the old bet once the new one is fully resolved.
            payslip.pop(slip_index)
        add_to_payslip(payslip, match, sign)
        return {"message": f"Added {teams}: {sign} @ {(match.get('odds') or {}).get(sign)}.",
                "payslip": payslip, "decision": decision}

    return {"message": "I did not understand the action", "payslip": payslip, "decision": decision}
