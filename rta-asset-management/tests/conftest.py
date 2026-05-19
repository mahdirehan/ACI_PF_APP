"""
Pytest configuration and hooks for RTA Asset Management test suite.

This module provides:
- Automatic Excel report generation after test runs
- Test result collection with metadata
"""

import pytest
from pathlib import Path

try:
    from tests.excel_reporter import ExcelTestReporter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


_reporter: "ExcelTestReporter" = None


def pytest_configure(config):
    """Initialize the Excel reporter at the start of the test session."""
    global _reporter
    
    if not EXCEL_AVAILABLE:
        return
    
    try:
        project_root = Path(__file__).parent.parent
        _reporter = ExcelTestReporter(output_dir=project_root)
        _reporter.start_session()
    except Exception as e:
        print(f"Warning: Could not initialize Excel reporter: {e}")
        _reporter = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results after each test execution."""
    outcome = yield
    report = outcome.get_result()
    
    if _reporter is None:
        return
    
    if report.when == "call":
        status = "PASS" if report.passed else ("FAIL" if report.failed else "SKIP")
        
        params = {}
        if hasattr(item, "callspec"):
            params = dict(item.callspec.params)
        
        docstring = item.function.__doc__ if hasattr(item, "function") else ""
        
        module_name = ""
        if hasattr(item, "module") and item.module is not None:
            module_name = item.module.__name__
        
        test_class = ""
        if hasattr(item, "cls") and item.cls is not None:
            test_class = item.cls.__name__
        
        result = {
            "name": item.name,
            "full_name": item.nodeid,
            "module": module_name,
            "class": test_class,
            "docstring": docstring,
            "params": params,
            "status": status,
            "duration_ms": report.duration * 1000,
            "longrepr": str(report.longrepr) if report.longrepr else "",
        }
        
        _reporter.add_result(result)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report after all tests complete."""
    global _reporter
    
    if _reporter is None:
        return
    
    if len(_reporter.results) == 0:
        return
    
    try:
        _reporter.end_session()
        report_path = _reporter.generate_report()
        
        print("\n" + "=" * 60)
        print("EXCEL TEST REPORT GENERATED")
        print("=" * 60)
        print(f"Location: {report_path}")
        print(f"Total tests: {len(_reporter.results)}")
        passed = sum(1 for r in _reporter.results if r.get('status') == 'PASS')
        failed = sum(1 for r in _reporter.results if r.get('status') == 'FAIL')
        print(f"Passed: {passed} | Failed: {failed}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        import traceback
        print(f"\nWarning: Could not generate Excel report: {e}")
        print("Traceback:")
        traceback.print_exc()
    finally:
        _reporter = None


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--no-excel",
        action="store_true",
        default=False,
        help="Disable Excel report generation",
    )
    parser.addoption(
        "--excel-output",
        action="store",
        default=None,
        help="Custom output directory for Excel report",
    )
