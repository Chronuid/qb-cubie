import json
import tkinter as tk
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Protocol


# ========== PROTOCOLS & DATACLASSES ===================================================================================

@dataclass
class ReviewData:
    """Kapselt das standardisierte Ergebnis einer RBT-Prüfung."""
    passed: bool
    report: Dict[str, Any] = field(default_factory=dict)


class Reviewer(Protocol):
    """Definiert den Vertrag für alle injizierbaren Prüfinstanzen."""
    def review(
            self,
            target: Optional[str],
            check: str
    ) -> ReviewData: ...


# ========== REVIEW-BASED-TESTING ======================================================================================

class RBT:
    """
    Orchestriert den Review-basierten Testablauf.
    """
    def __init__(
            self,
            check: str,
            target: Optional[Any] = None,
            reviewer: Optional[Reviewer] = None,
            tags: Optional[list[str]] = None
    ):
        self.check = check
        self.target = target
        self.reviewer = reviewer or HumanReviewer()
        self.tags = tags or []
        self._target_string: Optional[str] = None
        self._result: Optional[ReviewData] = None
        self._raw_json: Optional[str] = None


    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self) -> None:
        """Führt die Prüf-Pipeline sequenziell aus."""
        __tracebackhide__ = True
        self._arrange()
        self._review()
        self._report()


    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Bereitet die Eingabedaten für den Prüfer vor."""
        self._target_string = self._evaluate(self.target)

    def _review(self) -> None:
        """Delegiert die Prüfung an die injizierte Instanz."""
        self._result = self.reviewer.review(
            target=self._target_string,
            check=self.check
        )

    def _report(self) -> None:
        """Übergibt das finale Prüfergebnis mitsamt Payload an das Test-Framework."""
        __tracebackhide__ = True
        if self._result is None:
            raise RuntimeError("RBT Pipeline Error: Die Review-Phase hat kein Ergebnis geliefert.")
        payload_data = {"reviewer_report": self._result.report}
        payload = self._serialize(payload_data)
        assert self._result.passed, payload


    # ----- Utilities --------------------------------------------------------------------------------------------------

    @staticmethod
    def _evaluate(obj: Any) -> Optional[str]:
        """Wandelt das übergebene Zielobjekt in eine Zeichenkette um."""
        if obj is None or isinstance(obj, str):
            return obj
        return getattr(obj, "__name__", str(obj))

    def _serialize(self, data: Dict[str, Any]) -> str:
        self._raw_json = json.dumps(data, ensure_ascii=False)
        lines = ["\n--- RBT Report ---"]
        for key, value in data.get("reviewer_report", {}).items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


# ========== HUMAN-IN-THE-LOOP =========================================================================================

class HumanReviewer:
    """
    Stellt die interaktive Tkinter-basierte Prüfung bereit.
    """
    def __init__(self) -> None:
        self._target: Optional[str] = None
        self._check: str = ""
        self._passed: bool = False
        self._report_text: str = ""
        self._root: Optional[tk.Tk] = None
        self._text_widget: Optional[tk.Text] = None


    # ----- Services ---------------------------------------------------------------------------------------------------

    def review(self, target: Optional[str], check: str) -> ReviewData:
        """Führt den manuellen Review-Prozess durch."""
        self._target = target
        self._check = check
        self._run_gui()
        report_payload = {"text": self._report_text} if self._report_text else {}
        return ReviewData(passed=self._passed, report=report_payload)


    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _run_gui(self) -> None:
        """Initialisiert und startet das blockierende GUI-Fenster."""
        self._root = tk.Tk()
        if self._root is None:
            raise RuntimeError("GUI Error: Tkinter Root konnte nicht erstellt werden.")
        self._root.title("RBT - Manuelle Prüfung")
        self._root.attributes('-topmost', True)
        self._build_widgets()
        self._root.wait_window()

    def _build_widgets(self) -> None:
        """Konstruiert die visuellen UI-Elemente für das Fenster."""
        if self._root is None:
            raise RuntimeError("GUI Error: Root-Fenster ist nicht initialisiert.")
        if self._target:
            tk.Label(self._root, text=f"Target: {self._target}", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self._root, text=f"Check: {self._check}", font=("Arial", 12)).pack(pady=5)
        self._text_widget = tk.Text(self._root, height=8, width=60)
        self._text_widget.pack(pady=10, padx=20)
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Erstellt die Bestätigungs-Buttons für die binäre Entscheidung."""
        frame = tk.Frame(self._root)
        frame.pack(pady=10)
        tk.Button(frame, text="Bestanden (y)",
            bg="green",  fg="white", command=self._on_pass
        ).pack(side=tk.LEFT,padx=20)
        tk.Button(frame, text="Fehlgeschlagen (n)",
            bg="red", fg="white", command=self._on_fail
        ).pack(side=tk.RIGHT, padx=20)


    # ----- Utilities --------------------------------------------------------------------------------------------------

    def _on_pass(self) -> None:
        """Speichert das positive Ergebnis und schließt das Fenster."""
        self._passed = True
        self._finalize()

    def _on_fail(self) -> None:
        """Speichert das negative Ergebnis und schließt das Fenster."""
        self._passed = False
        self._finalize()

    def _finalize(self) -> None:
        """Liest den optionalen Report aus und beendet die UI-Schleife."""
        if self._root is None or self._text_widget is None:
            raise RuntimeError("GUI Error: UI-Komponenten fehlen beim Finalisieren.")
        self._report_text = self._text_widget.get("1.0", "end-1c").strip()
        self._root.destroy()