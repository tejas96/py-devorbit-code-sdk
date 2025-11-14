"""Tests for hooks system."""


from devorbit._hooks import (
    Hook,
    HookContext,
    HookRegistry,
    HookType,
    execute_hook,
    execute_hooks,
    list_hooks,
    load_hooks_from_config,
    register_hook,
    trigger_hook,
)


class TestHookType:
    """Test HookType enum."""

    def test_hook_types(self) -> None:
        """Test hook type values."""
        assert HookType.PRE_TOOL_CALL.value == "pre_tool_call"
        assert HookType.POST_TOOL_CALL.value == "post_tool_call"
        assert HookType.PRE_FILE_WRITE.value == "pre_file_write"
        assert HookType.POST_FILE_WRITE.value == "post_file_write"


class TestHookContext:
    """Test HookContext class."""

    def test_hook_context_creation(self) -> None:
        """Test creating hook context."""
        context = HookContext(
            hook_type=HookType.PRE_TOOL_CALL,
            data={"tool": "bash"},
            metadata={"user": "test"},
        )

        assert context.hook_type == HookType.PRE_TOOL_CALL
        assert context.data["tool"] == "bash"
        assert context.metadata["user"] == "test"


class TestHook:
    """Test Hook class."""

    def test_hook_creation(self) -> None:
        """Test creating a hook."""
        hook = Hook(
            name="test_hook",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
            enabled=True,
        )

        assert hook.name == "test_hook"
        assert hook.hook_type == HookType.PRE_COMMIT
        assert hook.command == "echo 'test'"
        assert hook.enabled is True

    def test_hook_should_run(self) -> None:
        """Test hook should_run method."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
            enabled=True,
        )

        context = HookContext(
            hook_type=HookType.PRE_COMMIT,
            data={},
            metadata={},
        )

        assert hook.should_run(context) is True

    def test_hook_should_not_run_disabled(self) -> None:
        """Test disabled hook should not run."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
            enabled=False,
        )

        context = HookContext(
            hook_type=HookType.PRE_COMMIT,
            data={},
            metadata={},
        )

        assert hook.should_run(context) is False

    def test_hook_should_not_run_wrong_type(self) -> None:
        """Test hook doesn't run for wrong type."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
            enabled=True,
        )

        context = HookContext(
            hook_type=HookType.POST_COMMIT,
            data={},
            metadata={},
        )

        assert hook.should_run(context) is False

    def test_hook_with_filter_condition(self) -> None:
        """Test hook with filter condition."""

        def filter_func(ctx: HookContext) -> bool:
            return ctx.data.get("allowed") is True

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_CALL,
            command="echo 'test'",
            enabled=True,
            filter_condition=filter_func,
        )

        # Should run with allowed=True
        context1 = HookContext(
            hook_type=HookType.PRE_TOOL_CALL,
            data={"allowed": True},
            metadata={},
        )
        assert hook.should_run(context1) is True

        # Should not run with allowed=False
        context2 = HookContext(
            hook_type=HookType.PRE_TOOL_CALL,
            data={"allowed": False},
            metadata={},
        )
        assert hook.should_run(context2) is False


class TestHookRegistry:
    """Test HookRegistry class."""

    def test_register_hook(self) -> None:
        """Test registering a hook."""
        registry = HookRegistry()
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
        )

        registry.register(hook)

        hooks = registry.get_hooks(HookType.PRE_COMMIT)
        assert len(hooks) == 1
        assert hooks[0].name == "test"

    def test_get_hooks_empty(self) -> None:
        """Test getting hooks when none registered."""
        registry = HookRegistry()

        hooks = registry.get_hooks(HookType.PRE_COMMIT)

        assert len(hooks) == 0

    def test_remove_hook(self) -> None:
        """Test removing a hook."""
        registry = HookRegistry()
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
        )

        registry.register(hook)
        assert len(registry.get_hooks(HookType.PRE_COMMIT)) == 1

        removed = registry.remove("test")

        assert removed is True
        assert len(registry.get_hooks(HookType.PRE_COMMIT)) == 0

    def test_clear_registry(self) -> None:
        """Test clearing registry."""
        registry = HookRegistry()
        hook1 = Hook(
            name="hook1",
            hook_type=HookType.PRE_COMMIT,
            command="echo '1'",
        )
        hook2 = Hook(
            name="hook2",
            hook_type=HookType.POST_COMMIT,
            command="echo '2'",
        )

        registry.register(hook1)
        registry.register(hook2)

        registry.clear()

        assert len(registry.get_hooks(HookType.PRE_COMMIT)) == 0
        assert len(registry.get_hooks(HookType.POST_COMMIT)) == 0

    def test_enable_disable(self) -> None:
        """Test enabling/disabling hooks."""
        registry = HookRegistry()

        assert registry.is_enabled() is True

        registry.disable()
        assert registry.is_enabled() is False

        registry.enable()
        assert registry.is_enabled() is True


class TestHookExecution:
    """Test hook execution."""

    def test_execute_hook_success(self) -> None:
        """Test executing a successful hook."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'success'",
            enabled=True,
        )

        context = HookContext(
            hook_type=HookType.PRE_COMMIT,
            data={},
            metadata={},
        )

        result = execute_hook(hook, context, timeout=5)

        assert result["success"] is True
        assert result["hook"] == "test"
        assert "success" in result["stdout"]

    def test_execute_hook_failure(self) -> None:
        """Test executing a failing hook."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="exit 1",
            enabled=True,
        )

        context = HookContext(
            hook_type=HookType.PRE_COMMIT,
            data={},
            metadata={},
        )

        result = execute_hook(hook, context, timeout=5)

        assert result["success"] is False
        assert result["returncode"] == 1

    def test_execute_hook_skipped(self) -> None:
        """Test skipping a hook."""
        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
            enabled=False,
        )

        context = HookContext(
            hook_type=HookType.PRE_COMMIT,
            data={},
            metadata={},
        )

        result = execute_hook(hook, context)

        assert result["skipped"] is True
        assert result["hook"] == "test"

    def test_execute_hooks_multiple(self) -> None:
        """Test executing multiple hooks."""
        registry = HookRegistry()

        hook1 = Hook(
            name="hook1",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'hook1'",
        )
        hook2 = Hook(
            name="hook2",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'hook2'",
        )

        registry.register(hook1)
        registry.register(hook2)

        results = execute_hooks(
            HookType.PRE_COMMIT,
            context_data={},
            registry=registry,
        )

        assert len(results) == 2
        assert all(r["success"] for r in results)

    def test_execute_hooks_registry_disabled(self) -> None:
        """Test hooks not executed when registry disabled."""
        registry = HookRegistry()
        registry.disable()

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_COMMIT,
            command="echo 'test'",
        )
        registry.register(hook)

        results = execute_hooks(
            HookType.PRE_COMMIT,
            registry=registry,
        )

        assert len(results) == 0


class TestHookConfiguration:
    """Test loading hooks from configuration."""

    def test_load_hooks_from_config(self) -> None:
        """Test loading hooks from config dictionary."""
        config = {
            "hooks": {
                "pre_commit": [
                    {
                        "name": "lint",
                        "command": "ruff check .",
                        "enabled": True,
                    },
                    {
                        "name": "format",
                        "command": "black .",
                        "enabled": False,
                    },
                ],
                "post_file_write": [
                    {
                        "name": "notify",
                        "command": "echo 'file written'",
                    },
                ],
            }
        }

        hooks = load_hooks_from_config(config)

        assert len(hooks) == 3

        lint_hook = next(h for h in hooks if h.name == "lint")
        assert lint_hook.hook_type == HookType.PRE_COMMIT
        assert lint_hook.enabled is True

        format_hook = next(h for h in hooks if h.name == "format")
        assert format_hook.enabled is False

    def test_load_hooks_invalid_type(self) -> None:
        """Test loading hooks with invalid type."""
        config = {
            "hooks": {
                "invalid_type": [
                    {
                        "name": "test",
                        "command": "echo 'test'",
                    },
                ],
            }
        }

        hooks = load_hooks_from_config(config)

        assert len(hooks) == 0

    def test_load_hooks_missing_fields(self) -> None:
        """Test loading hooks with missing fields."""
        config = {
            "hooks": {
                "pre_commit": [
                    {"name": "test"},  # Missing command
                    {"command": "echo 'test'"},  # Missing name
                ],
            }
        }

        hooks = load_hooks_from_config(config)

        assert len(hooks) == 0


class TestHookTools:
    """Test hook tools for agent use."""

    def test_list_hooks_tool(self) -> None:
        """Test list_hooks tool."""
        # Register a test hook
        register_hook("test", HookType.PRE_COMMIT, "echo 'test'")

        result = list_hooks()

        assert result["success"] is True
        assert result["count"] > 0
        assert any(h["name"] == "test" for h in result["hooks"])

    def test_list_hooks_filtered(self) -> None:
        """Test list_hooks with type filter."""
        register_hook("pre_hook", HookType.PRE_COMMIT, "echo 'pre'")
        register_hook("post_hook", HookType.POST_COMMIT, "echo 'post'")

        result = list_hooks("pre_commit")

        assert result["success"] is True
        hooks = result["hooks"]
        assert any(h["name"] == "pre_hook" for h in hooks)

    def test_trigger_hook_tool(self) -> None:
        """Test trigger_hook tool."""
        register_hook("test", HookType.PRE_COMMIT, "echo 'triggered'")

        result = trigger_hook("pre_commit", {"test_data": "value"})

        assert result["success"] is True
        assert result["executed"] > 0

    def test_trigger_hook_invalid_type(self) -> None:
        """Test trigger_hook with invalid type."""
        result = trigger_hook("invalid_type", {})

        assert "error" in result
        assert "Invalid hook type" in result["error"]

    def test_register_hook_function(self) -> None:
        """Test programmatic hook registration."""
        register_hook(
            name="custom_hook",
            hook_type=HookType.PRE_FILE_WRITE,
            command="echo 'custom'",
            enabled=True,
        )

        result = list_hooks("pre_file_write")

        assert result["success"] is True
        assert any(h["name"] == "custom_hook" for h in result["hooks"])
