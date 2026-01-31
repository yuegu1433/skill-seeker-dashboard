"""Editor Configuration Schemas.

This module contains Pydantic schemas for online editor configuration,
settings, sessions, and features.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict
from uuid import UUID

# Import enums
try:
    from app.file.models.file import FileType
except ImportError:
    FileType = Enum("FileType", {"DOCUMENT": "document", "IMAGE": "image", "VIDEO": "video", "AUDIO": "audio", "CODE": "code", "ARCHIVE": "archive", "OTHER": "other"})


class EditorTheme(str, Enum):
    """Editor theme enumeration."""
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"
    MONOKAI = "monokai"
    GITHUB = "github"
    Dracula = "dracula"
    SOLARIZED_LIGHT = "solarized_light"
    SOLARIZED_DARK = "solarized_dark"


class EditorMode(str, Enum):
    """Editor mode enumeration."""
    NORMAL = "normal"
    VIM = "vim"
    EMACS = "emacs"
    SUBLIME = "sublime"


class EditorLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    LESS = "less"
    JSON = "json"
    YAML = "yaml"
    YAMLML = "yamlml"
    XML = "xml"
    MARKDOWN = "markdown"
    TEXT = "text"
    SQL = "sql"
    GO = "go"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    JAVA_SCRIPT = "java_script"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"


class AutoSaveStrategy(str, Enum):
    """Auto-save strategy enumeration."""
    DISABLED = "disabled"
    TIMER = "timer"
    CHANGE = "change"
    BLUR = "blur"


class EditorSettings(BaseModel):
    """Schema for editor settings."""

    theme: EditorTheme = Field(default=EditorTheme.LIGHT, description="Editor theme")
    font_family: str = Field(default="Monaco, Consolas, monospace", description="Font family")
    font_size: int = Field(default=14, ge=8, le=72, description="Font size in pixels")
    line_height: float = Field(default=1.5, ge=1.0, le=3.0, description="Line height")
    tab_size: int = Field(default=4, ge=2, le=8, description="Tab size in spaces")
    word_wrap: bool = Field(default=True, description="Enable word wrap")
    line_numbers: bool = Field(default=True, description="Show line numbers")
    syntax_highlight: bool = Field(default=True, description="Enable syntax highlighting")
    indent_guides: bool = Field(default=True, description="Show indent guides")
    code_folding: bool = Field(default=True, description="Enable code folding")
    minimap: bool = Field(default=True, description="Show minimap")
    vim_mode: bool = Field(default=False, description="Enable Vim mode")
    emmet: bool = Field(default=True, description="Enable Emmet")
    bracket_pair_colorization: bool = Field(default=True, description="Enable bracket pair colorization")
    show_whitespace: bool = Field(default=False, description="Show whitespace characters")
    show_end_of_line: bool = Field(default=False, description="Show end of line characters")
    show_indent_guides: bool = Field(default=True, description="Show indent guides")
    show_print_margin: bool = Field(default=False, description="Show print margin")
    print_margin_column: int = Field(default=80, ge=0, le=200, description="Print margin column")
    highlight_active_line: bool = Field(default=True, description="Highlight active line")
    highlight_selected_word: bool = Field(default=True, description="Highlight selected word")
    auto_close_brackets: bool = Field(default=True, description="Auto close brackets")
    auto_close_tags: bool = Field(default=True, description="Auto close HTML tags")
    format_on_paste: bool = Field(default=True, description="Format on paste")
    format_on_type: bool = Field(default=True, description="Format on type")
    drag_and_drop: bool = Field(default=True, description="Enable drag and drop")
    multi_cursor: bool = Field(default=True, description="Enable multi cursor")


class AutoSaveSettings(BaseModel):
    """Schema for auto-save settings."""

    enabled: bool = Field(default=True, description="Enable auto-save")
    strategy: AutoSaveStrategy = Field(default=AutoSaveStrategy.TIMER, description="Auto-save strategy")
    interval: int = Field(default=30, ge=5, le=300, description="Auto-save interval in seconds")
    max_history: int = Field(default=50, ge=10, le=200, description="Maximum history entries")
    backup_enabled: bool = Field(default=True, description="Enable backup before save")


class SyntaxHighlightSettings(BaseModel):
    """Schema for syntax highlighting settings."""

    enabled: bool = Field(default=True, description="Enable syntax highlighting")
    theme: EditorTheme = Field(default=EditorTheme.LIGHT, description="Syntax highlight theme")
    font_size: Optional[int] = Field(default=None, ge=8, le=72, description="Syntax highlight font size")
    show_invisibles: bool = Field(default=False, description="Show invisible characters")
    highlight_scope: bool = Field(default=True, description="Highlight scope")
    show_gutter: bool = Field(default=True, description="Show gutter")
    gutter_line_numbers: bool = Field(default=True, description="Show gutter line numbers")


class EditorPlugin(BaseModel):
    """Schema for editor plugins."""

    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    enabled: bool = Field(default=True, description="Whether plugin is enabled")
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Plugin configuration")


class EditorKeyboardShortcut(BaseModel):
    """Schema for keyboard shortcuts."""

    action: str = Field(..., description="Action name")
    key: str = Field(..., description="Keyboard shortcut")
    when: Optional[str] = Field(None, description="Context condition")
    description: Optional[str] = Field(None, description="Action description")


class EditorConfig(BaseModel):
    """Schema for complete editor configuration."""

    settings: EditorSettings = Field(default_factory=EditorSettings, description="Editor settings")
    auto_save: AutoSaveSettings = Field(default_factory=AutoSaveSettings, description="Auto-save settings")
    syntax_highlight: SyntaxHighlightSettings = Field(default_factory=SyntaxHighlightSettings, description="Syntax highlighting settings")
    plugins: List[EditorPlugin] = Field(default_factory=list, description="Enabled plugins")
    keyboard_shortcuts: List[EditorKeyboardShortcut] = Field(default_factory=list, description="Custom keyboard shortcuts")
    custom_css: Optional[str] = Field(None, description="Custom CSS")
    custom_js: Optional[str] = Field(None, description="Custom JavaScript")
    extensions: List[str] = Field(default_factory=list, description="Enabled extensions")
    language_overrides: Dict[EditorLanguage, Dict[str, Any]] = Field(default_factory=dict, description="Language-specific overrides")


class EditorSession(BaseModel):
    """Schema for editor session."""

    file_id: UUID = Field(..., description="File ID being edited")
    user_id: str = Field(..., description="User ID")
    session_id: UUID = Field(default_factory=UUID, description="Session ID")
    language: EditorLanguage = Field(default=EditorLanguage.TEXT, description="Programming language")
    config: EditorConfig = Field(default_factory=EditorConfig, description="Editor configuration")
    content: Optional[str] = Field(None, description="Current content")
    cursor_position: Optional[Dict[str, int]] = Field(None, description="Cursor position")
    selections: Optional[List[Dict[str, Any]]] = Field(None, description="Current selections")
    scroll_position: Optional[Dict[str, int]] = Field(None, description="Scroll position")
    is_dirty: bool = Field(default=False, description="Whether content has unsaved changes")
    last_saved_at: Optional[datetime] = Field(None, description="Last save timestamp")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Session last update time")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    collaborators: List[str] = Field(default_factory=list, description="Collaborator user IDs")
    is_readonly: bool = Field(default=False, description="Whether session is read-only")
    version: int = Field(default=1, description="Session version")


class EditorSessionResponse(BaseModel):
    """Schema for editor session response."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    file_id: UUID
    user_id: str
    language: EditorLanguage
    config: EditorConfig
    content: Optional[str]
    cursor_position: Optional[Dict[str, int]]
    selections: Optional[List[Dict[str, Any]]]
    scroll_position: Optional[Dict[str, int]]
    is_dirty: bool
    last_saved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    collaborators: List[str]
    is_readonly: bool
    version: int


class EditorChange(BaseModel):
    """Schema for editor changes."""

    session_id: UUID = Field(..., description="Session ID")
    version: int = Field(..., description="Change version")
    changes: List[Dict[str, Any]] = Field(..., description="List of changes")
    author_id: str = Field(..., description="Author of changes")
    timestamp: datetime = Field(default_factory=datetime.now, description="Change timestamp")


class EditorCollaborator(BaseModel):
    """Schema for editor collaborators."""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: Optional[str] = Field(None, description="User email")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    cursor_position: Optional[Dict[str, int]] = Field(None, description="Cursor position")
    selection: Optional[Dict[str, Any]] = Field(None, description="Current selection")
    color: str = Field(default="#007acc", description="User color in editor")
    is_active: bool = Field(default=True, description="Whether user is active")
    last_seen: datetime = Field(default_factory=datetime.now, description="Last seen timestamp")


class EditorCommand(BaseModel):
    """Schema for editor commands."""

    command: str = Field(..., description="Command name")
    args: Optional[Dict[str, Any]] = Field(None, description="Command arguments")
    timestamp: datetime = Field(default_factory=datetime.now, description="Command timestamp")


class EditorSearch(BaseModel):
    """Schema for editor search."""

    query: str = Field(..., description="Search query")
    case_sensitive: bool = Field(default=False, description="Case sensitive search")
    whole_word: bool = Field(default=False, description="Match whole word")
    regex: bool = Field(default=False, description="Use regular expressions")
    replace: Optional[str] = Field(None, description="Replace text")
    replace_all: bool = Field(default=False, description="Replace all occurrences")


class EditorAction(BaseModel):
    """Schema for editor actions."""

    action_type: Literal["save", "undo", "redo", "format", "find", "replace"] = Field(..., description="Action type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Action timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Action metadata")


# Utility functions
def get_language_from_extension(extension: str) -> EditorLanguage:
    """Get editor language from file extension."""
    extension = extension.lower().lstrip('.')
    language_map = {
        "py": EditorLanguage.PYTHON,
        "java": EditorLanguage.JAVA,
        "js": EditorLanguage.JAVASCRIPT,
        "ts": EditorLanguage.TYPESCRIPT,
        "html": EditorLanguage.HTML,
        "css": EditorLanguage.CSS,
        "scss": EditorLanguage.SCSS,
        "less": EditorLanguage.LESS,
        "json": EditorLanguage.JSON,
        "yml": EditorLanguage.YAML,
        "yaml": EditorLanguage.YAML,
        "xml": EditorLanguage.XML,
        "md": EditorLanguage.MARKDOWN,
        "txt": EditorLanguage.TEXT,
        "sql": EditorLanguage.SQL,
        "go": EditorLanguage.GO,
        "rs": EditorLanguage.RUST,
        "c": EditorLanguage.C,
        "cpp": EditorLanguage.CPP,
        "h": EditorLanguage.C,
        "php": EditorLanguage.PHP,
        "rb": EditorLanguage.RUBY,
        "swift": EditorLanguage.SWIFT,
        "kt": EditorLanguage.KOTLIN,
    }
    return language_map.get(extension, EditorLanguage.TEXT)


def get_supported_languages() -> List[EditorLanguage]:
    """Get list of supported programming languages."""
    return list(EditorLanguage)


def validate_editor_config(config: EditorConfig) -> bool:
    """Validate editor configuration."""
    try:
        # Validate settings
        if config.settings.font_size < 8 or config.settings.font_size > 72:
            return False

        # Validate auto-save
        if config.auto_save.interval < 5 or config.auto_save.interval > 300:
            return False

        # Validate plugins
        plugin_names = [p.name for p in config.plugins]
        if len(plugin_names) != len(set(plugin_names)):
            return False  # Duplicate plugin names

        return True
    except Exception:
        return False


def get_default_config_for_language(language: EditorLanguage) -> EditorConfig:
    """Get default editor configuration for specific language."""
    base_settings = EditorSettings()

    # Language-specific overrides
    if language in [EditorLanguage.PYTHON, EditorLanguage.JAVA, EditorLanguage.JAVASCRIPT, EditorLanguage.TYPESCRIPT]:
        base_settings.tab_size = 4
        base_settings.syntax_highlight = True
        base_settings.auto_close_brackets = True
    elif language in [EditorLanguage.HTML, EditorLanguage.CSS, EditorLanguage.SCSS, EditorLanguage.LESS]:
        base_settings.auto_close_tags = True
        base_settings.format_on_paste = True

    return EditorConfig(settings=base_settings)
