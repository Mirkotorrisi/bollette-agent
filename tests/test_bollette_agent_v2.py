import unittest
from unittest.mock import MagicMock, patch

import bollette_agent_v2 as agent
from third_parties import jev

MATCHES = [
    {"id": "a1", "matchId": "inter-juve", "sport_key": "serie_a", "teams": ["Inter", "Juventus"],
     "start": "2026-10-12T18:45:00Z", "odds": {"home": 2.1, "draw": 3.2, "away": 3.5, "over": 1.8, "under": 2.0}},
    {"id": "b2", "matchId": "roma-lazio", "sport_key": "serie_a", "teams": ["Roma", "Lazio"],
     "start": "2026-10-13T20:45:00Z", "odds": {"home": 2.4, "draw": 3.1, "away": 2.9, "gg": 1.7, "ng": 2.1}},
]


def choice(selected, probabilities=None):
    return {"type": "choice", "choice": selected, "confidence": 0.9,
            "probabilities": probabilities or {selected: 0.9}}


def noul(p):
    return {"type": "noul", "noul": p}


class AgentV2Test(unittest.TestCase):
    def setUp(self):
        agent.PAYSLIPS_V2.clear()
        patcher = patch.object(agent, "get_matches", return_value=MATCHES)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_with(self, *responses, session=None, user_input="x"):
        with patch.object(agent, "decide", side_effect=[{"answers": r} for r in responses]) as decide:
            if session is None:
                res = agent.startup(user_input)
            else:
                res = agent.process_action(session, user_input)
        return res, decide

    def test_add_resolves_match_then_sign(self):
        res, decide = self.run_with(
            {"intent": choice("add"), "match_mentioned": noul(0.97), "match_0": choice("M0001")},
            {"sign": choice("gg")},
            user_input="Roma Lazio goal",
        )
        self.assertEqual(res["payslip"], [{"id": "b2", "sport_key": "serie_a", "matchId": "roma-lazio",
                                           "teams": ["Roma", "Lazio"], "start": "2026-10-13T20:45:00Z",
                                           "odd": 1.7, "sign": "gg"}])
        sign_state, sign_questions = decide.call_args_list[1].args[:2]
        self.assertEqual(sign_state["match"], {"home_team": "Roma", "away_team": "Lazio"})
        # Only signs with available odds are offered, plus "unspecified".
        self.assertEqual(set(sign_questions["sign"]["criteria"]), {"home", "draw", "away", "gg", "ng", "unspecified"})

    def test_add_unknown_match_does_not_ask_for_sign(self):
        res, decide = self.run_with(
            {"intent": choice("add"), "match_mentioned": noul(0.08), "match_0": choice("M0000")},
            user_input="Barcelona 1",
        )
        self.assertEqual(res["payslip"], [])
        self.assertEqual(decide.call_count, 1)
        self.assertIn("couldn't find that match", res["message"])

    def test_unspecified_sign_asks_user(self):
        res, _ = self.run_with(
            {"intent": choice("add"), "match_mentioned": noul(0.9), "match_0": choice("M0000")},
            {"sign": choice("unspecified")},
        )
        self.assertEqual(res["payslip"], [])
        self.assertIn("Which result", res["message"])

    def test_session_survives_empty_slip(self):
        res, _ = self.run_with({"intent": choice("other"), "match_mentioned": noul(0.1), "match_0": choice("M0000")})
        self.assertIn(res["id"], agent.PAYSLIPS_V2)

    def test_remove_targets_slip_line(self):
        agent.PAYSLIPS_V2["s"] = [{"id": "a1", "teams": ["Inter", "Juventus"], "sign": "home", "odd": 2.1},
                                  {"id": "b2", "teams": ["Roma", "Lazio"], "sign": "gg", "odd": 1.7}]
        res, decide = self.run_with(
            {"intent": choice("remove"), "slip_mentioned": noul(0.95), "slip_target": choice("P01"),
             "match_mentioned": noul(0.9), "match_0": choice("M0001")},
            session="s", user_input="remove Roma",
        )
        self.assertEqual([b["id"] for b in res["payslip"]], ["a1"])
        self.assertIn("P01| Roma - Lazio, sign: gg", decide.call_args.args[0]["bet_slip"])

    def test_replace_keeps_old_bet_when_new_sign_unclear(self):
        agent.PAYSLIPS_V2["s"] = [{"id": "a1", "teams": ["Inter", "Juventus"], "sign": "home", "odd": 2.1}]
        res, _ = self.run_with(
            {"intent": choice("replace"), "slip_mentioned": noul(0.9), "slip_target": choice("P00"),
             "match_mentioned": noul(0.9), "match_0": choice("M0001")},
            {"sign": choice("unspecified")},
            session="s",
        )
        self.assertEqual([b["id"] for b in res["payslip"]], ["a1"])

    def test_replace_swaps_bet(self):
        agent.PAYSLIPS_V2["s"] = [{"id": "a1", "teams": ["Inter", "Juventus"], "sign": "home", "odd": 2.1}]
        res, _ = self.run_with(
            {"intent": choice("replace"), "slip_mentioned": noul(0.9), "slip_target": choice("P00"),
             "match_mentioned": noul(0.9), "match_0": choice("M0001")},
            {"sign": choice("home")},
            session="s", user_input="replace Inter with Roma 1",
        )
        self.assertEqual([(b["id"], b["sign"]) for b in res["payslip"]], [("b2", "home")])

    def checkout(self, amount_answer, user_input, openai_amount=None):
        agent.PAYSLIPS_V2["s"] = [{"id": "a1", "odd": 2.0}, {"id": "b2", "odd": 1.5}]
        with patch.object(agent, "openai_amount", return_value=openai_amount) as fallback:
            res, _ = self.run_with({"intent": choice("checkout"), "amount": amount_answer},
                                   session="s", user_input=user_input)
        return res, fallback

    def test_checkout_computes_max_win_and_closes_session(self):
        res, fallback = self.checkout(choice("20"), "checkout 20")
        self.assertEqual((res["amount"], res["multiplier"], res["max_win"]), (20.0, 3.0, 60.0))
        self.assertEqual(res["decision"]["amount_source"], "jev")
        self.assertNotIn("s", agent.PAYSLIPS_V2)
        fallback.assert_not_called()

    def test_checkout_amount_in_words_uses_jev(self):
        res, fallback = self.checkout(choice("10", {"10": 0.92}), "punta dieci euro")
        self.assertEqual(res["amount"], 10.0)
        fallback.assert_not_called()

    def test_checkout_snapped_amount_falls_back_to_openai(self):
        # Jev picked the nearest common stake, but the user typed 7,33.
        res, fallback = self.checkout(choice("7", {"7": 0.7}), "checkout 7,33", openai_amount=7.33)
        self.assertEqual(res["amount"], 7.33)
        self.assertEqual(res["decision"]["amount_source"], "openai")
        fallback.assert_called_once_with("checkout 7,33")

    def test_checkout_other_amount_falls_back_to_openai(self):
        res, _ = self.checkout(choice("other"), "gioca settecentoventidue euro", openai_amount=722.0)
        self.assertEqual(res["amount"], 722.0)

    def test_checkout_low_confidence_falls_back_to_openai(self):
        res, fallback = self.checkout(choice("15", {"15": 0.4, "50": 0.35}), "checkout una quindicina", openai_amount=15.0)
        self.assertEqual(res["decision"]["amount_source"], "openai")
        fallback.assert_called_once()

    def test_checkout_without_amount_keeps_session(self):
        res, fallback = self.checkout(choice("none"), "ok confirm")
        self.assertNotIn("amount", res)
        self.assertIn("How much", res["message"])
        self.assertIn("s", agent.PAYSLIPS_V2)
        fallback.assert_not_called()

    def test_checkout_failed_fallback_asks_amount(self):
        res, _ = self.checkout(choice("other"), "checkout 7,33", openai_amount=None)
        self.assertNotIn("amount", res)
        self.assertIn("s", agent.PAYSLIPS_V2)


class MainQuestionsTest(unittest.TestCase):
    def test_amount_question_fits_choice_limit(self):
        criteria = agent.build_main_questions([], [])["amount"]["criteria"]
        self.assertLessEqual(len(criteria), jev.MAX_CHOICE_OPTIONS)
        self.assertTrue({"0.5", "1", "10", "25", "1000", "none", "other"} <= set(criteria))

    def test_large_catalog_is_chunked(self):
        matches = [{"teams": [f"T{i}", f"U{i}"]} for i in range(600)]
        questions = agent.build_main_questions(matches, [])
        chunks = [q for k, q in questions.items() if k.startswith("match_") and k != "match_mentioned"]
        self.assertEqual([len(q["criteria"]) for q in chunks], [255, 255, 90])
        self.assertIn("M0510", chunks[2]["criteria"])

    def test_pick_match_prefers_most_peaked_chunk(self):
        matches = [{"teams": [f"T{i}", f"U{i}"]} for i in range(300)]
        answers = {
            "match_mentioned": noul(0.9),
            "match_0": choice("M0010", {"M0010": 0.2, "M0011": 0.2}),
            "match_1": choice("M0270", {"M0270": 0.95}),
        }
        match, probability = agent.pick_match(answers, matches)
        self.assertIs(match, matches[270])
        self.assertEqual(probability, 0.95)


class JevClientTest(unittest.TestCase):
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}, clear=False)
    @patch("third_parties.jev.requests.post")
    def test_sends_decisions_request(self, post):
        post.return_value = MagicMock(status_code=200, json=lambda: {"model": "m", "answers": {"q": noul(1)}})
        res = jev.decide({"a": 1}, {"q": {"type": "noul", "instructions": "?"}}, session_id="s1")
        self.assertEqual(res["answers"]["q"]["noul"], 1)
        url = post.call_args.args[0]
        body = post.call_args.kwargs["json"]
        self.assertEqual(url, "https://openrouter.ai/api/alpha/decisions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual((body["model"], body["session_id"]), ("typesafe/jev-1.13", "s1"))

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}, clear=False)
    @patch("third_parties.jev.requests.post")
    def test_raises_on_api_error(self, post):
        post.return_value = MagicMock(status_code=402, json=lambda: {"error": {"code": 402, "message": "Insufficient credits"}})
        with self.assertRaises(jev.JevError) as ctx:
            jev.decide("s", {})
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertIn("Insufficient credits", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
