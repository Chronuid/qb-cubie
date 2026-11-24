<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](./docs/.assets/cubie-logo-written.png)

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Lösung der noch fehlschlagenden Tests mit einem vollständig autonomen TGD-Fluss.


## Kontext

Wir haben heute in mehreren Abschnitten versucht die Bugs 007, 002 und 003 zu addressieren. Anschließend habe ich `make test-all` ausgeführt. Die meisten Tests scheinen zu bestehen. Allerdings sagt die Test-Suite, dass noch vier Tests fehlschlagen.  
Präzise gesagt ist es das Test-Modul:  'tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py'  

### Ergebnis
```text 
Testing started at 20:34 ...
Launching pytest with arguments /home/symphonie/PycharmProjects/cubie/tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py --no-header --no-summary -q in /home/symphonie/PycharmProjects/cubie

============================= test session starts ==============================
collecting ... collected 6 items


========================= 4 failed, 2 passed in 1.59s ==========================

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_cubie_doc_frame_1_updates_nav_and_preserves_slots FAILED [ 16%]
tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:242 (test_ebt_cubie_doc_frame_1_updates_nav_and_preserves_slots)
def test_ebt_cubie_doc_frame_1_updates_nav_and_preserves_slots() -> None:
        """Verifies that CUBIE_DOC_FRAME_1 updates nav/footer, injects the epistemic notice, and protects title, intro, disclaimer, and body."""
        expected = {
            "preserves_title": True,
            "preserves_intro": True,
            "preserves_disclaimer": True,
            "injects_epistemic_notice": True,
            "epistemic_notice_count": 1,
            "preserves_body": True,
            "fixes_banner_and_alt": True,
            "fixes_footer_alt": True,
            "removes_error_alt": True,
            "uses_div_align_center": True,
        }
        EBT(
            target=_run_preset_update_scenario,
            arena=TempFS(),
            pre=WorldState(args=("frame_1",)),
            post=WorldState(returns=expected),
            custom_id="docframe_preset_1_slot_protection",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_docframe_preset_1_slot_protection_139af5e1666641f4b61901083bb7d459_0':
E       Target: _run_preset_update_scenario
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'preserves_title': True, 'preserves_intro': True, 'preserves_disclaimer': True, 'injects_epistemic_notice': True, 'epistemic_notice_count': 1, 'preserves_body': True, 'fixes_banner_and_alt': True, 'fixes_footer_alt': True, 'removes_error_alt': True, 'uses_div_align_center': True} | Actual {'preserves_title': True, 'preserves_intro': True, 'preserves_disclaimer': True, 'injects_epistemic_notice': False, 'epistemic_notice_count': 1, 'preserves_body': True, 'fixes_banner_and_alt': True, 'fixes_footer_alt': True, 'removes_error_alt': True, 'uses_div_align_center': True} (Mismatch)

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:262: AssertionError

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_cubie_doc_frame_2_syncs_provenance_and_preserves_extra_slots PASSED [ 33%]
tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_cubie_doc_frame_3_updates_router_and_protects_manual_content FAILED [ 50%]
tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:280 (test_ebt_cubie_doc_frame_3_updates_router_and_protects_manual_content)
def test_ebt_cubie_doc_frame_3_updates_router_and_protects_manual_content() -> None:
        """Verifies that CUBIE_DOC_FRAME_3 rebuilds zone='router' tables, injects the epistemic notice, and avoids double dividers."""
        keys = (
            "rebuilds_router_table",
            "removes_stale_row",
            "preserves_pre_text",
            "preserves_manual_table",
            "injects_epistemic_notice",
            "no_double_dividers_in_head",
        )
        EBT(
            target=_run_preset_update_scenario,
            arena=TempFS(),
            pre=WorldState(args=("frame_3",)),
            post=WorldState(returns=dict.fromkeys(keys, True)),
            custom_id="docframe_preset_3_router_update",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_docframe_preset_3_router_update_a24f6a8790b9458ea58b365687598d54_0':
E       Target: _run_preset_update_scenario
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'rebuilds_router_table': True, 'removes_stale_row': True, 'preserves_pre_text': True, 'preserves_manual_table': True, 'injects_epistemic_notice': True, 'no_double_dividers_in_head': True} | Actual {'rebuilds_router_table': True, 'removes_stale_row': True, 'preserves_pre_text': True, 'preserves_manual_table': True, 'injects_epistemic_notice': False, 'no_double_dividers_in_head': True} (Mismatch)

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:296: AssertionError

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_bug_007_epistemic_notice_preserved_injected_and_deduplicated FAILED [ 66%]
tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:299 (test_ebt_bug_007_epistemic_notice_preserved_injected_and_deduplicated)
def test_ebt_bug_007_epistemic_notice_preserved_injected_and_deduplicated() -> None:
        """Verifies BUG-007: DocFrame.update() never overwrites the epistemic notice in 4-segment headers and never duplicates it in 3-segment headers."""
        expected = {
            "has_canonical_epistemic_notice": True,
            "epistemic_count_exactly_one": True,
            "no_double_dividers_in_head": True,
            "preserves_custom_disclaimer": True,
        }
        EBT(
            target=_run_bug_007_epistemic_preservation_scenario,
            arena=TempFS(),
            pre=[
                WorldState(args=("four_segment",)),
                WorldState(args=("legacy_three_segment",)),
                WorldState(args=("bare_two_segment",)),
            ],
            post=WorldState(returns=expected),
            custom_id="docframe_bug_007_epistemic_notice_anchor",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_docframe_bug_007_epistemic_notice_anchor_6286b1a574394bbcb6f333ebc550480b_0':
E       Target: _run_bug_007_epistemic_preservation_scenario
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'has_canonical_epistemic_notice': True, 'epistemic_count_exactly_one': True, 'no_double_dividers_in_head': True, 'preserves_custom_disclaimer': True} | Actual {'has_canonical_epistemic_notice': False, 'epistemic_count_exactly_one': True, 'no_double_dividers_in_head': True, 'preserves_custom_disclaimer': True} (Mismatch)

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:317: AssertionError

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_central_presets_module_serves_as_single_source_of_truth FAILED [ 83%]
tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:320 (test_ebt_central_presets_module_serves_as_single_source_of_truth)
def test_ebt_central_presets_module_serves_as_single_source_of_truth() -> None:
        """Verifies that presets.py centralizes head/foot templates and the epistemic notice anchor."""
        keys = (
            "has_canonical_notice_text",
            "has_notice_block",
            "exports_std_head_blocks",
            "exports_std_footer_blocks",
            "reexported_in_services",
        )
        EBT(
            target=_inspect_central_presets_module,
            pre=WorldState(),
            post=WorldState(returns=dict.fromkeys(keys, True)),
            custom_id="docframe_central_presets_ssot",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_docframe_central_presets_ssot_d98bebbe18a6495b8e171e60c0813e5b_0':
E       Target: _inspect_central_presets_module
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'has_canonical_notice_text': True, 'has_notice_block': True, 'exports_std_head_blocks': True, 'exports_std_footer_blocks': True, 'reexported_in_services': True} | Actual {'has_canonical_notice_text': False, 'has_notice_block': True, 'exports_std_head_blocks': True, 'exports_std_footer_blocks': True, 'reexported_in_services': False} (Mismatch)

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:334: AssertionError

tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py::test_ebt_docframe_update_idempotence PASSED [100%]
Process finished with exit code 1
```

Ich weis nicht ob es während der Addressierung von BUG-007 schon fehlschlug, unterwegs entstanden ist und nicht aufgedeckt wurde, oder erst durch mich entstand. Ich habe unterwegs übrigens das Preset bzw das 'EPISTEMIC_NOTICE_TEXT'-Objekt mutiert. Ich wollte nämlich eine zentrale Stelle zum Pflegen von diesem NOTICE-Text. Ich habe auf die schnelle leider keine Docs gefunden, die mir erklärten wie das geht. Also habe ich den Text einfach dort mutiert, wo er zentral steht.

---

@KNOWN_ISSUES.md  

@docs/GUIDE_Quality-Assurance.md  
@docs/GUIDE_Contract-Design.md  
@docs/GUIDE_Expect-Flags.md  
@docs/GUIDE_Quantifiers.md  
@docs/GUIDE_TGD.md  

@docs/dev/DEV-GUIDE_Agent-Reports.md  
@AGENT_REPORT-3.md  

## Auftrag

Addressiere die fehlschlagenden Tests vollständig autonom mit dem TGD-Flow.  
Dokumentiere den Verlauf in @AGENT_REPORT-3.md

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
