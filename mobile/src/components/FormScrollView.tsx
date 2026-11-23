import { useCallback, useEffect, useImperativeHandle, useRef, type Ref, type RefObject } from 'react';
import { Keyboard, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, TextInput, type ScrollViewProps, type View } from 'react-native';

const fieldClearance = 12;

export function FormScrollView({ ref, onFocus, onLayout, ...props }: ScrollViewProps & { ref?: Ref<ScrollView> }) {
  const scroll = useRef<ScrollView>(null);
  const content = useRef<View>(null);
  const frame = useRef<number | null>(null);
  useImperativeHandle(ref, () => scroll.current!, []);

  const revealFocusedField = useCallback(() => {
    if (Platform.OS === 'web') return;
    if (frame.current !== null) cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      frame.current = null;
      const field = TextInput.State.currentlyFocusedInput();
      const scrollView = scroll.current;
      const viewport = scrollView?.getNativeScrollRef();
      if (!field || !scrollView || !viewport || !content.current) return;

      field.measureLayout(content.current, (_x, contentY) => {
        viewport.measureInWindow((_left, top, _width, height) => {
          field.measureInWindow((_fieldLeft, fieldTop, _fieldWidth, fieldHeight) => {
            if (scroll.current !== scrollView || field !== TextInput.State.currentlyFocusedInput() || !height || !fieldHeight) return;
            const keyboardTop = Keyboard.metrics()?.screenY;
            const bottom = Math.min(top + height, keyboardTop ?? Infinity) - fieldClearance;
            if (bottom <= top) return;
            const delta = fieldTop < top
              ? fieldTop - top
              : Math.max(0, fieldTop + fieldHeight - bottom);
            if (delta !== 0) {
              scrollView.scrollTo({ y: Math.max(0, contentY - (fieldTop - top) + delta), animated: true });
            }
          });
        });
      }, () => {
        // The focused input can belong to another screen or modal.
      });
    });
  }, []);

  useEffect(() => {
    if (Platform.OS === 'web') return;
    const subscription = Keyboard.addListener('keyboardDidShow', revealFocusedField);
    return () => {
      subscription.remove();
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, [revealFocusedField]);

  const form = (
    <ScrollView
      automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}
      keyboardDismissMode="on-drag"
      keyboardShouldPersistTaps="handled"
      {...props}
      ref={scroll}
      innerViewRef={content as RefObject<View>}
      onFocus={(event) => {
        onFocus?.(event);
        revealFocusedField();
      }}
      onLayout={(event) => {
        onLayout?.(event);
        revealFocusedField();
      }}
    />
  );
  return Platform.OS === 'android' ? (
    <KeyboardAvoidingView behavior="height" style={styles.frame}>
      {form}
    </KeyboardAvoidingView>
  ) : form;
}

const styles = StyleSheet.create({ frame: { flex: 1 } });
