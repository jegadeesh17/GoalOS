"""Regression tests for `reload_settings()` in configs/settings.py.

`reload_settings()` re-reads `.env`/environment variables and mutates the
existing module-level `settings` singleton in place (via `setattr` over
`Settings.model_fields`) so that references already bound elsewhere via
`from config.settings import settings` or `from configs.settings import
settings` observe the fresh values without needing to re-import. These
tests exercise that in-place mutation behavior directly, since it was
previously untested.
"""

from configs.settings import reload_settings


class TestReloadSettingsSanity:
  def test_reload_with_no_env_changes_does_not_raise(self):
    reload_settings()

  def test_reload_does_not_create_a_new_settings_instance(self):
    from configs.settings import settings as settings_ref

    before_id = id(settings_ref)
    result = reload_settings()

    assert id(result) == before_id
    assert id(settings_ref) == before_id


class TestReloadSettingsMutatesExistingReferences:
  def test_prebound_reference_sees_new_value_after_reload(self, monkeypatch):
    # Bind a local reference the way a real module would at its own import
    # time, *before* the env var changes and *before* reload_settings() is
    # called.
    from config.settings import settings as bound_settings

    original_log_level = bound_settings.LOG_LEVEL
    assert original_log_level != "CRITICAL"

    try:
      monkeypatch.setenv("LOG_LEVEL", "CRITICAL")
      reload_settings()

      # The whole point of in-place mutation: a reference obtained before
      # the reload must reflect the new value without re-importing.
      assert bound_settings.LOG_LEVEL == "CRITICAL"
    finally:
      bound_settings.LOG_LEVEL = original_log_level

  def test_config_and_configs_reexports_stay_in_sync_after_reload(self, monkeypatch):
    import config.settings as config_settings_module
    import configs.settings as configs_settings_module

    # `config.settings.settings` is a re-export of the exact same object as
    # `configs.settings.settings`, so mutating one must be visible via the
    # other.
    assert config_settings_module.settings is configs_settings_module.settings

    original_environment = configs_settings_module.settings.ENVIRONMENT
    assert original_environment != "staging"

    try:
      monkeypatch.setenv("ENVIRONMENT", "staging")
      reload_settings()

      assert config_settings_module.settings.ENVIRONMENT == "staging"
      assert configs_settings_module.settings.ENVIRONMENT == "staging"
    finally:
      configs_settings_module.settings.ENVIRONMENT = original_environment
