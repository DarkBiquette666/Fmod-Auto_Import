# Code Quality & Architecture Improvement Plan

This document outlines technical debt and proposes architectural improvements to transition the FMOD Importer Tool from a prototype script to a robust, scalable application.

## 1. Architecture: Composition over Inheritance (De-coupling Mixins)

### The Problem
The current application relies heavily on **Mixins** (`WidgetsMixin`, `DialogsMixin`, `ImportMixin`, etc.) combined into a single `FmodImporterGUI` class.
- **"God Object" Anti-Pattern:** Through multiple inheritance, `FmodImporterGUI` becomes a massive namespace where everything has access to everything (`self.project`, `self.root`, etc.).
- **Tight Coupling:** It is impossible to test the "Import Logic" without instantiating the entire "GUI Window".
- **Maintainability:** Tracing where a variable like `self.selected_bank_id` is modified requires searching through 10 different files.

### The Solution: Composition & MVC/MVP
Refactor the main application to use **Composition**. Break down the monolithic GUI into distinct components or controllers.

*   **View Components:** Create standalone classes for UI sections that take their dependencies via constructor.
    ```python
    class BankSelectorView:
        def __init__(self, parent, project_model):
            self.model = project_model
            self.frame = ttk.LabelFrame(parent, text="Bank")
            # ... builds its own widgets ...
    ```
*   **Controller/Presenter:** Separate the "Business Logic" (what happens when I click Import) from the "View" (drawing buttons).

**Benefit:** Independent, testable components. Easier to rearrange the UI.

## 2. XML Abstraction Layer (Data Models)

### The Problem
The codebase manually constructs XML strings or uses `xml.etree.ElementTree` imperatively within Manager classes (`BankManager`, `BusManager`).
- **Fragility:** If FMOD changes its XML schema (e.g., property naming), we have to hunt-and-peck through scattered `ET.SubElement(...)` calls.
- **Verbosity:** The code is cluttered with low-level XML manipulation details that obscure the high-level intent.

### The Solution: Data Transfer Objects (DTOs) & Serializers
Create strong Python types (Data Classes) for FMOD concepts and dedicated serializers.

```python
@dataclass
class FmodBank:
    uuid: str
    name: str
    type: str = "bank"

class FmodXmlSerializer:
    def serialize_bank(self, bank: FmodBank) -> ET.Element:
        # Single place where XML structure is defined
        pass
```

**Benefit:** "Type-safe" development. Centralized XML logic. Support for multiple FMOD versions becomes easier (just switch serializers).

## 3. Command Pattern for Actions

### The Problem
Actions like "Create Folder" or "Rename Bank" are simple methods. To support features like **Undo/Redo** or **Batch Operations**, we currently rely on ad-hoc logic. The recent "Pending/Deferred" refactor is a step towards this, but it's specific to the Import flow.

### The Solution
Implement the **Command Pattern**.

```python
class Command(ABC):
    def execute(self): pass
    def undo(self): pass

class CreateBankCommand(Command):
    def execute(self):
        # Create bank logic
    def undo(self):
        # Delete the bank we just created
```

**Benefit:** Enables global Undo/Redo (Ctrl+Z). Allows logging of user actions. Simplifies the "Deferred/Transactional" logic by just building a list of Commands to execute later.

## 4. Automated Testing (Unit Tests)

### The Problem
There are **zero** automated tests. Every refactor relies on manual "click-testing" by the developer. This is high-risk and slow.

### The Solution
Integrate `unittest` (standard library) or `pytest`.

### Test Suite Checklist
- [x] **`test_naming_pattern.py`**: Validate regex logic, iterator stripping, separators, and flexible matching.
- [ ] **`test_matcher.py`**: Verify fuzzy matching logic (Levenshtein distance) and best-match selection.
- [ ] **`test_managers.py`**: Test `BankManager`, `BusManager`, `EventFolderManager` ensuring `commit=False` works correctly.
- [ ] **`test_preset_resolver.py`**: Test resolution logic (UUID vs Path) and pending item creation.
- [ ] **`test_xml_loader.py`**: Test parsing of FMOD XML structures and error handling for malformed files.
- [ ] **`test_integration_import.py`**: Mock end-to-end import flow (generating JSON without running FMOD).

**Benefit:** Fearless refactoring. Immediate regression detection.

## 5. Robust Error Handling & Logging

### The Problem
The code frequently uses generic `try... except Exception` blocks that catch *everything* (including coding errors like typos) and show them in a generic `messagebox.showerror`. This makes debugging on user machines difficult.

### The Solution
*   **Custom Exceptions:** Define `FmodProjectError`, `ValidationError`, `ResourceNotFoundError` to handle expected errors specifically.
*   **Logging:** Implement the standard Python `logging` module. Write logs to a file (`fmod_importer.log`).
    *   *Info:* "User loaded project X"
    *   *Error:* Stack traces for crashes.

**Benefit:** Better user experience (clearer error messages). Easier debugging of reported issues.
