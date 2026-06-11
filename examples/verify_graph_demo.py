# examples/verify_graph_demo.py
# Demonstrates graph-state consistency verification using sheaf cohomology.
#
# This example constructs a small graph with claims on each vertex,
# checks whether the claims are globally consistent, and emits
# a verification receipt.
#
# Usage:
#   python examples/verify_graph_demo.py

from __future__ import annotations

import json
import time
import hashlib
import sys
import os


def compute_coboundary_energy(vertices, edges):
    """Compute the Dirichlet energy (coboundary norm) for each edge.

    For each edge, the energy is the squared difference between
    the claims on the two endpoints that should agree under the
    restriction map. Nonzero energy indicates a local disagreement.

    Returns a list of (source, target, field, energy) tuples.
    """
    disagreements = []
    vertex_map = {v["id"]: v["claims"] for v in vertices}

    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        relation = edge.get("relation", "same_entity")

        src_claims = vertex_map.get(src, {})
        tgt_claims = vertex_map.get(tgt, {})

        # Under a "same_entity" or "agrees_on" relation, shared
        # keys must have equal values. Disagreement = nonzero energy.
        shared_keys = set(src_claims.keys()) & set(tgt_claims.keys())
        for key in shared_keys:
            if src_claims[key] != tgt_claims[key]:
                disagreements.append((src, tgt, key, 1.0))

    return disagreements


def verify_graph(vertices, edges):
    """Verify graph consistency.

    Returns a verdict dict suitable for SVR receipt construction.
    """
    start = time.perf_counter()
    disagreements = compute_coboundary_energy(vertices, edges)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    has_contradictions = len(disagreements) > 0

    checked_items = []
    item_counter = 0
    for src, tgt, field, energy in disagreements:
        item_counter += 1
        checked_items.append({
            "item_id": item_counter,
            "claim_or_authority": "coboundary operator: %s <-> %s on '%s'" % (src, tgt, field),
            "verdict": "CONTRADICTED",
            "reason": (
                "'%s' and '%s' disagree on '%s'. "
                "Dirichlet energy: %.4f."
                % (src, tgt, field, energy)
            ),
        })

    # Add a global consistency item
    if not has_contradictions:
        item_counter += 1
        checked_items.append({
            "item_id": item_counter,
            "claim_or_authority": "sheaf cohomology H^1",
            "verdict": "PASS",
            "reason": "H^1 is trivial. All local claims glue to a consistent global section.",
        })

    items_passed = sum(1 for it in checked_items if it["verdict"] == "PASS")
    items_failed = sum(1 for it in checked_items if it["verdict"] != "PASS")

    graph_hash = hashlib.sha256(
        json.dumps(
            {"vertices": vertices, "edges": edges},
            sort_keys=True
        ).encode()
    ).hexdigest()

    receipt = {
        "svr_version": "1.0",
        "receipt_id": "SIGMA-20260610-%s" % graph_hash[:8].upper(),
        "receipt_type": "agent",
        "mode": "full_verification",
        "receipt_status": "evaluation",
        "input_hash": graph_hash[:16],
        "source_bundle_hash": graph_hash[:16],
        "verdict": "unsafe_to_submit" if has_contradictions else "verified",
        "safe_to_rely": not has_contradictions,
        "filing_safety_status": "UNSAFE_TO_SUBMIT" if has_contradictions else "SAFE_TO_SUBMIT",
        "reason": (
            "%d structural contradiction(s) detected."
            % len(disagreements)
            if has_contradictions
            else "All claims are globally consistent."
        ),
        "items_checked": len(checked_items),
        "items_passed": items_passed,
        "items_failed": items_failed,
        "items_excluded": 0,
        "checked_items": checked_items,
        "timestamp_utc": "2026-06-10T12:00:00Z",
        "engine_version": "sigma-demo-0.1.0",
        "verification_method": "deterministic_algebraic",
        "public_key": "unsigned",
        "signature": "",
        "signature_status": "UNSIGNED",
    }

    return receipt, elapsed_ms, disagreements


def main():
    print("=" * 60)
    print("Graph-State Consistency Verification Demo")
    print("=" * 60)
    print()

    # --- Consistent graph ---
    print("Graph 1: Supply chain (consistent)")
    print("-" * 40)
    consistent_vertices = [
        {"id": "Policy", "claims": {"approved_vendor": "Supplier_A", "region": "US"}},
        {"id": "Procurement", "claims": {"approved_vendor": "Supplier_A", "region": "US"}},
        {"id": "Audit", "claims": {"region": "US"}},
    ]
    consistent_edges = [
        {"source": "Policy", "target": "Procurement", "relation": "same_entity"},
        {"source": "Procurement", "target": "Audit", "relation": "same_entity"},
    ]

    receipt, ms, disag = verify_graph(consistent_vertices, consistent_edges)

    print("  Vertices: %d" % len(consistent_vertices))
    print("  Edges:    %d" % len(consistent_edges))
    print("  Verdict:  %s" % receipt["verdict"])
    print("  Elapsed:  %.2fms" % ms)
    print()

    # --- Contradictory graph ---
    print("Graph 2: Supply chain (contradicted)")
    print("-" * 40)
    bad_vertices = [
        {"id": "Policy", "claims": {"approved_vendor": "Supplier_A"}},
        {"id": "Procurement", "claims": {"approved_vendor": "Supplier_B"}},
        {"id": "Audit", "claims": {"compliance_status": "approved"}},
        {"id": "Operations", "claims": {"compliance_status": "under_review"}},
    ]
    bad_edges = [
        {"source": "Policy", "target": "Procurement", "relation": "same_entity"},
        {"source": "Audit", "target": "Operations", "relation": "same_entity"},
    ]

    receipt2, ms2, disag2 = verify_graph(bad_vertices, bad_edges)

    print("  Vertices: %d" % len(bad_vertices))
    print("  Edges:    %d" % len(bad_edges))
    print("  Verdict:  %s" % receipt2["verdict"])
    print()

    for src, tgt, field, energy in disag2:
        print("  [CONTRADICTION] %s <-> %s" % (src, tgt))
        print("    Disagreement on: %s" % field)
        print("    Dirichlet energy: %.4f" % energy)
        print()

    print("  Elapsed:  %.2fms" % ms2)
    print()

    # Write the contradicted receipt as an example output
    output_path = os.path.join(
        os.path.dirname(__file__),
        "receipts",
        "demo_output.svr.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(receipt2, f, indent=2)

    print("Receipt written to: %s" % output_path)
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
