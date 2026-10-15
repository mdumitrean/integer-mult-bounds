"""run2_sk2model.py: run2.py but with sk2.Round.model (the original model builder) instead of gen2.model_lean,
to cross-check a lean-model INFEASIBLE verdict on a small target."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen2, sk2
gen2.FastRound.model = sk2.Round.model
gen2.FastRound.solve = sk2.Round.solve
import run2
if __name__ == '__main__':
    run2.main()
