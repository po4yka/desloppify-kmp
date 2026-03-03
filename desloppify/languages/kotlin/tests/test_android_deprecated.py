"""Tests for Android deprecated APIs detector."""

from __future__ import annotations

from desloppify.languages.kotlin.detectors.android_deprecated import (
    detect_android_deprecated_apis,
)


def _has_kind(findings, kind):
    return any(f["detail"]["kind"] == kind for f in findings)


def _scan(code: str, ext: str = ".kt") -> list[dict]:
    path = f"src/main/java/com/example/App{ext}"
    return detect_android_deprecated_apis([path], read_fn=lambda _: code)


class TestWorldReadableWritable:
    def test_detects_world_readable(self):
        code = "val fd = openFileOutput(name, MODE_WORLD_READABLE)"
        assert _has_kind(_scan(code), "world_readable_writable")

    def test_no_flag_private_mode(self):
        code = "val fd = openFileOutput(name, MODE_PRIVATE)"
        assert not _has_kind(_scan(code), "world_readable_writable")


class TestSqlInjectionRisk:
    def test_detects_raw_query_concat(self):
        code = 'db.rawQuery("SELECT * FROM users WHERE id = " + userId, null)'
        assert _has_kind(_scan(code), "sql_injection_risk")

    def test_no_flag_parameterized(self):
        code = 'db.rawQuery("SELECT * FROM users WHERE id = ?", arrayOf(userId))'
        assert not _has_kind(_scan(code), "sql_injection_risk")


class TestDeprecatedAsyncTask:
    def test_detects_asynctask_import(self):
        code = "import android.os.AsyncTask"
        assert _has_kind(_scan(code), "deprecated_asynctask")

    def test_no_flag_coroutines(self):
        code = "import kotlinx.coroutines.launch"
        assert not _has_kind(_scan(code), "deprecated_asynctask")


class TestDeprecatedIntentService:
    def test_detects_intentservice_import(self):
        code = "import android.app.IntentService"
        assert _has_kind(_scan(code), "deprecated_intentservice")

    def test_no_flag_workmanager(self):
        code = "import androidx.work.WorkManager"
        assert not _has_kind(_scan(code), "deprecated_intentservice")


class TestDeprecatedLocalBroadcast:
    def test_detects_localbroadcast(self):
        code = "LocalBroadcastManager.getInstance(context).sendBroadcast(intent)"
        assert _has_kind(_scan(code), "deprecated_localbroadcast")

    def test_no_flag_flow(self):
        code = "val flow = MutableSharedFlow<Event>()"
        assert not _has_kind(_scan(code), "deprecated_localbroadcast")


class TestOldSupportLibrary:
    def test_detects_support_v4(self):
        code = "import android.support.v4.app.Fragment"
        assert _has_kind(_scan(code), "old_support_library")

    def test_no_flag_androidx(self):
        code = "import androidx.fragment.app.Fragment"
        assert not _has_kind(_scan(code), "old_support_library")


class TestDeprecatedKotlinAndroidExt:
    def test_detects_synthetic_import(self):
        code = "import kotlinx.android.synthetic.main.activity_main.*"
        assert _has_kind(_scan(code), "deprecated_kotlin_android_ext")

    def test_no_flag_view_binding(self):
        code = "val binding = ActivityMainBinding.inflate(layoutInflater)"
        assert not _has_kind(_scan(code), "deprecated_kotlin_android_ext")

    def test_scans_java_files(self):
        code = "import android.os.AsyncTask;"
        assert _has_kind(_scan(code, ".java"), "deprecated_asynctask")

    def test_skips_non_source_files(self):
        findings = detect_android_deprecated_apis(
            ["readme.md"], read_fn=lambda _: "AsyncTask"
        )
        assert len(findings) == 0
