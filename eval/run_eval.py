# TODO: implement
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run planninggraph evaluation")
    parser.add_argument("--stage", type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    raise NotImplementedError(f"Stage {args.stage} evaluation not yet implemented")

if __name__ == "__main__":
    main()
