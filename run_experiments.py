#!/usr/bin/env python3
"""Reproduce the examples and finite consistency checks from the paper."""

import argparse
import csv
import random
import time
from pathlib import Path

from gc_semantics import (
    Affected, And, Apply, Atom, CLAIM, Contribute, EVIDENCE, Introduce,
    Justify, Not, Query, Record, Revise, State, Warrant, access_warrant,
    conjunction_warrant, grounded_continuation,
)


def by_expr(expression):
    return lambda state: state.find(expression)


def running_examples():
    f_p, h_p, d_p = Atom("f_P"), Atom("h_P"), And(Atom("f_P"), Atom("h_P"))
    state = State({"operator", "assistant"}, {"f_P", "h_P"})
    Apply(Contribute("operator", f_p, EVIDENCE), state)
    Apply(Query("assistant", h_p), state)
    Apply(Contribute("operator", h_p, EVIDENCE), state)
    Apply(Justify("assistant", d_p, (by_expr(f_p), by_expr(h_p)),
                  conjunction_warrant()), state)
    assert set(state.records) == state.grounded_records()

    before = state.grounded_records()
    Apply([
        Introduce("f_T"),
        Revise("operator", by_expr(f_p)),
        Contribute("operator", Atom("f_T"), EVIDENCE),
        Contribute("operator", Not(f_p), EVIDENCE),
    ], state)
    expected = {state.find(h_p), state.find(Atom("f_T")), state.find(Not(f_p))}
    assert state.grounded_records() == expected
    assert state.invalid_fixed_point() == set(state.records) - expected
    assert Affected(before, state) == {state.find(d_p)}

    # Grounding is record-level: another grounded record with the same
    # expression does not rescue an unsupported claim.
    is_grounded, _ = grounded_continuation(
        state, "assistant", Contribute("assistant", h_p, CLAIM)
    )
    assert not is_grounded

    p, q, r, s, z = map(Atom, "pqrsz")
    state = State({"a", "b", "c", "v", "reg"}, set("pqrsz"))
    for actor, expression in (("a", p), ("b", q), ("c", r)):
        Apply(Contribute(actor, expression, EVIDENCE), state)
    bad = Warrant("w_three", 3, lambda premises, conclusion: False)
    Apply(Justify("v", z, (by_expr(p), by_expr(q), by_expr(r)), bad), state)
    assert state.find(z) not in state.grounded_records()
    Apply(Introduce("auditor", is_agent=True), state)
    Apply(Contribute("reg", s, EVIDENCE), state)
    good = access_warrant((p, q, r, s), "w_access")
    Apply(Justify("auditor", z, (by_expr(p), by_expr(q), by_expr(r), by_expr(s)),
                  good, target=by_expr(z)), state)
    assert state.find(z) in state.grounded_records()

    # Evidence is a grounding base even when an incoming justification is stored.
    t = Atom("t")
    Apply(Introduce("t"), state)
    Apply(Contribute("a", t, EVIDENCE), state)
    identity = Warrant("w_id", 1, lambda premises, conclusion: premises[0] == conclusion)
    snapshot = (list(state.records), set(state.edges), set(state.standing))
    try:
        Apply(Justify("a", t, (by_expr(t),), identity, target=by_expr(t)), state)
        raise AssertionError("a cyclic justification was accepted")
    except ValueError as error:
        assert "cycle" in str(error)
    assert snapshot == (state.records, state.edges, state.standing)


def random_state(rng, size):
    names = {f"p{i}" for i in range(size)}
    state = State({"a"}, names)
    records = [Record(i, Atom(f"p{i}"), frozenset({"a"})) for i in range(size)]
    state.records = records
    state.standing = set(records)
    state.evidence = set(records[:max(1, size // 8)])
    for conclusion_index in range(max(1, size // 8), size):
        alternatives = rng.randint(0, 3)
        for edge_no in range(alternatives):
            width = rng.randint(1, min(4, conclusion_index))
            premises = frozenset(rng.sample(records[:conclusion_index], width))
            licensed = rng.random() >= 0.2
            warrant = Warrant(
                f"w{conclusion_index}_{edge_no}", width,
                lambda _premises, _conclusion, allowed=licensed: allowed,
            )
            state.edges.add((premises, warrant, records[conclusion_index]))
    assert state.well_formed()
    return state


def randomized_checks(trials, seed):
    rng = random.Random(seed)
    for _ in range(trials):
        state = random_state(rng, rng.randint(8, 60))
        standing = list(state.standing)
        for record in rng.sample(standing, rng.randint(0, min(5, len(standing)))):
            state.standing.remove(record)
        grounded = state.grounded_records()
        assert grounded == state.grounded_records_worklist()
        invalid = state.invalid_fixed_point()
        assert invalid == state.invalid_fixed_point_worklist()
        assert invalid == set(state.records) - grounded


def scaling(sizes, seed, output):
    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for size in sizes:
        state = random_state(rng, size)
        started = time.perf_counter()
        state.grounded_records_worklist()
        elapsed = time.perf_counter() - started
        premise_occurrences = sum(len(premises) for premises, _, _ in state.edges)
        rows.append((size, premise_occurrences, elapsed))
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("records", "premise_occurrences", "grounding_seconds"))
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=800)
    parser.add_argument("--seed", type=int, default=20260902)
    parser.add_argument("--scale", action="store_true")
    args = parser.parse_args()
    running_examples()
    randomized_checks(args.trials, args.seed)
    if args.scale:
        scaling((1000, 2000, 4000, 8000), args.seed,
                Path(__file__).parent / "results" / "scaling.csv")
    print(f"All examples and {args.trials} randomized checks passed.")


if __name__ == "__main__":
    main()
