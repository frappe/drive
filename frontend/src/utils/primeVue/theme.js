// src/utils/primeVue/theme.js
import { definePreset } from '@primevue/themes';

export const customTheme = definePreset({
  semantic: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#0149C1', // Primary color của bạn
      600: '#013a9c',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554'
    },
    // Định nghĩa màu chữ trong theme
    text: {
      color: '#222222',           // Màu chữ chính
      muted: '#555555',          // Màu chữ phụ
      disabled: '#b0b0b0',       // Màu chữ disabled
      inverse: '#ffffff'         // Màu chữ trên nền tối
    },
    colorScheme: {
      light: {
        primary: {
          color: '#0149C1',
          inverseColor: '#ffffff',
          hoverColor: '#013a9c',
          activeColor: '#013a9c'
        },
        // Text colors cho light mode
        text: {
          color: '#171717',         // Màu chữ chính
          secondaryColor: '#404040', // Màu chữ phụ
          mutedColor: '#888888',    // Màu chữ mờ
          disabledColor: '#b0b0b0', // Màu chữ disabled
          inverseColor: '#ffffff'   // Màu chữ ngược
        },
        highlight: {
          background: '#D4E1F9',
          focusBackground: '#D4E1F9',
          color: '#0149C1',         // Màu chữ highlight
          focusColor: '#0149C1'     // Màu chữ focus
        },
        surface: {
          0: '#ffffff',
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617'
        }
      },
      dark: {
        primary: {
          color: '#0149C1',
          inverseColor: '#ffffff',
          hoverColor: '#013a9c',
          activeColor: '#013a9c'
        },
        // Text colors cho dark mode
        text: {
          color: '#ffffff',         // Màu chữ chính cho dark
          secondaryColor: '#e2e8f0', // Màu chữ phụ cho dark
          mutedColor: '#94a3b8',    // Màu chữ mờ cho dark
          disabledColor: '#64748b', // Màu chữ disabled cho dark
          inverseColor: '#222222'   // Màu chữ ngược cho dark
        },
        highlight: {
          background: 'rgba(212, 225, 249, 0.16)',
          focusBackground: 'rgba(212, 225, 249, 0.24)',
          color: 'rgba(212, 225, 249, 0.87)',
          focusColor: 'rgba(212, 225, 249, 0.87)'
        },
        surface: {
          0: '#ffffff',
          50: '#0f172a',
          100: '#1e293b',
          200: '#334155',
          300: '#475569',
          400: '#64748b',
          500: '#94a3b8',
          600: '#cbd5e1',
          700: '#e2e8f0',
          800: '#f1f5f9',
          900: '#f8fafc',
          950: '#ffffff'
        }
      }
    }
  }
});

// CSS variables được generate từ theme
export const cssVariables = {
  // Primary colors
  '--p-primary-color': '#0149C1',
  '--p-primary-contrast-color': '#ffffff',
  '--p-primary-hover-color': '#013a9c',
  '--p-primary-active-color': '#013a9c',
  
  // Surface colors
  '--p-surface-0': '#ffffff',
  '--p-surface-50': '#f8fafc',
  '--p-surface-100': '#f1f5f9',
  '--p-surface-200': '#e2e8f0',
  '--p-surface-300': '#cbd5e1',
  '--p-surface-400': '#94a3b8',
  '--p-surface-500': '#64748b',
  '--p-surface-600': '#475569',
  '--p-surface-700': '#334155',
  '--p-surface-800': '#1e293b',
  '--p-surface-900': '#0f172a',
  '--p-surface-950': '#020617',
  
  // Text colors - Đây là nơi định nghĩa màu chữ chính
  '--p-text-color': '#222222',              // Màu chữ chính
  '--p-text-secondary-color': '#555555',    // Màu chữ phụ
  '--p-text-muted-color': '#888888',        // Màu chữ mờ
  '--p-text-disabled-color': '#b0b0b0',     // Màu chữ disabled
  '--p-text-inverse-color': '#ffffff',      // Màu chữ ngược (trên nền tối)
  
  // Component specific text colors
  '--p-button-text-primary-color': '#ffffff',
  '--p-button-text-secondary-color': '#222222',
  '--p-input-text-color': '#222222',
  '--p-dropdown-text-color': '#222222',
  '--p-datatable-header-text-color': '#222222',
  '--p-datatable-row-text-color': '#222222',
  '--p-dialog-title-text-color': '#222222',
  '--p-menu-item-text-color': '#222222',
  
  // Content colors  
  '--p-content-color': '#222222',
  '--p-content-hover-color': '#555555',
  '--p-content-active-color': '#0149C1',
  
  // Highlight colors
  '--p-highlight-background': '#D4E1F9',
  '--p-highlight-color': '#0149C1',
  '--p-highlight-focus-background': '#D4E1F9',
  '--p-highlight-focus-color': '#0149C1',
  
  // Form colors
  '--p-form-field-color': '#222222',
  '--p-form-field-placeholder-color': '#b0b0b0',
  '--p-form-field-focus-color': '#222222',
  '--p-form-field-invalid-color': '#e53935',
  
  // State colors với text
  '--p-error-color': '#e53935',
  '--p-error-text-color': '#ffffff',
  '--p-success-color': '#43a047',
  '--p-success-text-color': '#ffffff',
  '--p-info-color': '#1976d2',
  '--p-info-text-color': '#ffffff',
  '--p-warning-color': '#ffa000',
  '--p-warning-text-color': '#ffffff'
};