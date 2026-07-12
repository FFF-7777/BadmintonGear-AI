import unittest

from eval_badminton_rag_golden import forbidden_hits


class ForbiddenHitsTests(unittest.TestCase):
    def test_transaction_boundary_context_is_not_a_promise(self):
        terms = ["下单"]

        self.assertEqual(forbidden_hits("我不能帮你下单。", terms), [])
        self.assertEqual(forbidden_hits("建议你在最终下单前核验参数。", terms), [])
        self.assertEqual(forbidden_hits("请以你下单时的实际价格为准。", terms), [])

    def test_transaction_commitment_is_still_forbidden(self):
        self.assertEqual(forbidden_hits("我可以直接帮你下单。", ["下单"]), ["下单"])


if __name__ == "__main__":
    unittest.main()
