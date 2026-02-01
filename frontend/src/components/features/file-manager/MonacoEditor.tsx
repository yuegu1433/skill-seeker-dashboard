/**
 * MonacoEditor Component
 *
 * Monaco Editor wrapper with auto-save and syntax highlighting.
 */

import React, { useEffect, useRef } from 'react';
import * as monaco from 'monaco-editor';

interface MonacoEditorProps {
  value: string;
  language: string;
  onChange?: (value: string) => void;
  onSave?: () => void;
  readOnly?: boolean;
  theme?: 'vs-dark' | 'vs-light' | 'hc-black';
  height?: string | number;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  value,
  language,
  onChange,
  onSave,
  readOnly = false,
  theme = 'vs-dark',
  height = '100%',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create editor instance
    const editor = monaco.editor.create(containerRef.current, {
      value,
      language,
      theme,
      readOnly,
      automaticLayout: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
      fontLigatures: true,
      lineNumbers: 'on',
      renderWhitespace: 'selection',
      bracketPairColorization: { enabled: true },
      guides: {
        bracketPairs: true,
        indentation: true,
      },
      suggest: {
        showKeywords: true,
        showSnippets: true,
        showFunctions: true,
        showConstructors: true,
        showFields: true,
        showVariables: true,
        showClasses: true,
        showStructs: true,
        showInterfaces: true,
        showModules: true,
        showProperties: true,
        showEvents: true,
        showOperators: true,
        showUnits: true,
        showValues: true,
        showConstants: true,
        showEnums: true,
        showEnumMembers: true,
        showTypeParameters: true,
        showIssues: true,
        showUsers: true,
        showColors: true,
        showFiles: true,
        showReferences: true,
        showFolders: true,
      },
      quickSuggestions: {
        other: true,
        comments: true,
        strings: true,
      },
      wordWrap: 'on',
      formatOnPaste: true,
      formatOnType: true,
      tabSize: 2,
      insertSpaces: true,
      detectIndentation: true,
      rulers: [80, 120],
      folding: true,
      foldingHighlight: true,
      showFoldingControls: 'always',
    });

    editorRef.current = editor;

    // Handle content changes
    const disposable = editor.onDidChangeModelContent(() => {
      const currentValue = editor.getValue();
      onChange?.(currentValue);
    });

    // Handle save shortcut
    const saveDisposable = editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      () => {
        onSave?.();
      }
    );

    return () => {
      disposable.dispose();
      saveDisposable.dispose();
      editor.dispose();
    };
  }, [language, theme, readOnly, onChange, onSave]);

  // Update value when prop changes
  useEffect(() => {
    if (editorRef.current && value !== editorRef.current.getValue()) {
      const position = editorRef.current.getPosition();
      editorRef.current.setValue(value);
      if (position) {
        editorRef.current.setPosition(position);
      }
    }
  }, [value]);

  return <div ref={containerRef} style={{ width: '100%', height }} />;
};
