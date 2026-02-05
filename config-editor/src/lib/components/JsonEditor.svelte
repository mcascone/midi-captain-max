<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { EditorState } from '@codemirror/state';
  import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
  import { json } from '@codemirror/lang-json';
  import { oneDark } from '@codemirror/theme-one-dark';
  import { defaultKeymap } from '@codemirror/commands';

  interface Props {
    value?: string;
    readonly?: boolean;
    onchange?: (value: string) => void;
  }

  let { value = '', readonly = false, onchange }: Props = $props();
  
  let container: HTMLDivElement;
  let view: EditorView | undefined;

  onMount(() => {
    const state = EditorState.create({
      doc: value,
      extensions: [
        lineNumbers(),
        highlightActiveLine(),
        json(),
        oneDark,
        keymap.of(defaultKeymap),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            const newValue = update.state.doc.toString();
            onchange?.(newValue);
          }
        }),
        EditorState.readOnly.of(readonly),
      ],
    });

    view = new EditorView({
      state,
      parent: container,
    });
  });

  onDestroy(() => {
    view?.destroy();
  });

  // Update content when value prop changes externally
  $effect(() => {
    if (view && value !== view.state.doc.toString()) {
      view.dispatch({
        changes: {
          from: 0,
          to: view.state.doc.length,
          insert: value,
        },
      });
    }
  });
</script>

<div class="editor-wrapper" bind:this={container}></div>

<style>
  .editor-wrapper {
    height: 100%;
    overflow: auto;
    border: 1px solid #404040;
    border-radius: 4px;
  }
  
  .editor-wrapper :global(.cm-editor) {
    height: 100%;
  }
  
  .editor-wrapper :global(.cm-scroller) {
    font-family: 'SF Mono', Monaco, 'Courier New', monospace;
    font-size: 14px;
  }
</style>
