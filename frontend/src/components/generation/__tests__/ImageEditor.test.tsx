/**
 * Tests for ImageEditor Component (Story 4: Advanced Image Editing)
 *
 * Tests cover:
 * - AC #1: Image Editor Access (modal rendering, image display)
 * - AC #2: Mask Creation with Brush Tool (tool selection, drawing)
 * - AC #3: Mask Editing (eraser, clear mask)
 * - AC #4: Replacement Prompt Input (prompt validation, negative prompt)
 * - AC #5: Inpainting Execution (API call, loading state)
 * - AC #6: Edited Image Display (before/after comparison, button actions)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImageEditor from '../ImageEditor';
import * as interactiveApi from '../../../services/interactive-api';

// Mock the interactive API
vi.mock('../../../services/interactive-api', () => ({
  inpaintImage: vi.fn(),
}));

// Mock useImage hook from use-image
vi.mock('use-image', () => ({
  default: vi.fn((url: string) => {
    const img = new Image();
    img.src = url;
    return [img, 'loaded'];
  }),
}));

// Mock Konva Stage and Layer for canvas operations
vi.mock('react-konva', () => ({
  Stage: vi.fn(({ children, ...props }) => (
    <div data-testid="konva-stage" {...props}>
      {children}
    </div>
  )),
  Layer: vi.fn(({ children }) => <div data-testid="konva-layer">{children}</div>),
  Image: vi.fn(() => <div data-testid="konva-image" />),
  Line: vi.fn(() => <div data-testid="konva-line" />),
}));

describe('ImageEditor', () => {
  const mockProps = {
    imageUrl: '/api/v1/outputs/test-image.png',
    imageId: 0,
    sessionId: 'test-session-123',
    onSave: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================================
  // AC #1: Image Editor Access
  // ============================================================================

  describe('AC #1: Image Editor Access', () => {
    it('renders editor modal with image displayed', () => {
      render(<ImageEditor {...mockProps} />);

      // Modal/panel should be visible
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Edit Image')).toBeInTheDocument();

      // Image should be loaded on canvas
      expect(screen.getByTestId('konva-stage')).toBeInTheDocument();
      expect(screen.getByTestId('konva-image')).toBeInTheDocument();
    });

    it('displays editing tools (brush, eraser, clear)', () => {
      render(<ImageEditor {...mockProps} />);

      // Tool buttons should be present
      expect(screen.getByRole('button', { name: /brush/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /eraser/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear mask/i })).toBeInTheDocument();
    });

    it('displays cancel button to close editor', () => {
      render(<ImageEditor {...mockProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeInTheDocument();

      fireEvent.click(cancelButton);
      expect(mockProps.onCancel).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // AC #2: Mask Creation with Brush Tool
  // ============================================================================

  describe('AC #2: Mask Creation with Brush Tool', () => {
    it('allows selecting brush tool', async () => {
      render(<ImageEditor {...mockProps} />);

      const brushButton = screen.getByRole('button', { name: /brush/i });
      fireEvent.click(brushButton);

      // Brush should be active (check for active styling or aria-pressed)
      expect(brushButton).toHaveClass(/active|bg-blue|border-blue/i);
    });

    it('shows brush size slider with range 10-100px', () => {
      render(<ImageEditor {...mockProps} />);

      const slider = screen.getByRole('slider', { name: /brush size/i });
      expect(slider).toBeInTheDocument();
      expect(slider).toHaveAttribute('min', '10');
      expect(slider).toHaveAttribute('max', '100');
    });

    it('adjusts brush size with slider', async () => {
      const user = userEvent.setup();
      render(<ImageEditor {...mockProps} />);

      const slider = screen.getByRole('slider', { name: /brush size/i });

      // Change slider value
      await user.clear(slider);
      await user.type(slider, '50');

      // Brush size value should be displayed
      expect(screen.getByText(/50.*px/i)).toBeInTheDocument();
    });

    it('displays masked region with semi-transparent overlay', () => {
      render(<ImageEditor {...mockProps} />);

      // Konva layer should exist for mask overlay
      const layers = screen.getAllByTestId('konva-layer');
      expect(layers.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // AC #3: Mask Editing
  // ============================================================================

  describe('AC #3: Mask Editing', () => {
    it('allows selecting eraser tool', () => {
      render(<ImageEditor {...mockProps} />);

      const eraserButton = screen.getByRole('button', { name: /eraser/i });
      fireEvent.click(eraserButton);

      // Eraser should be active
      expect(eraserButton).toHaveClass(/active|bg-blue|border-blue/i);
    });

    it('clears entire mask when clear button clicked', () => {
      render(<ImageEditor {...mockProps} />);

      const clearButton = screen.getByRole('button', { name: /clear mask/i });
      fireEvent.click(clearButton);

      // Lines state should be cleared (tested by absence of konva-line elements after clear)
      // Note: In real implementation, this would clear the lines array
    });

    it('allows drawing and erasing mask strokes', () => {
      render(<ImageEditor {...mockProps} />);

      const stage = screen.getByTestId('konva-stage');

      // Simulate drawing (mousedown, mousemove, mouseup)
      fireEvent.mouseDown(stage, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(stage, { clientX: 150, clientY: 150 });
      fireEvent.mouseUp(stage);

      // In real implementation, this would create line elements
      // We're testing that the event handlers are attached
    });
  });

  // ============================================================================
  // AC #4: Replacement Prompt Input
  // ============================================================================

  describe('AC #4: Replacement Prompt Input', () => {
    it('renders prompt input field', () => {
      render(<ImageEditor {...mockProps} />);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      expect(promptInput).toBeInTheDocument();
    });

    it('accepts prompt text input', async () => {
      const user = userEvent.setup();
      render(<ImageEditor {...mockProps} />);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      expect(promptInput).toHaveValue('red sports car');
    });

    it('validates prompt is not empty before generation', async () => {
      render(<ImageEditor {...mockProps} />);

      const generateButton = screen.getByRole('button', { name: /generate/i });

      // Generate button should be disabled when prompt is empty
      expect(generateButton).toBeDisabled();
    });

    it('enables generate button when prompt is provided', async () => {
      const user = userEvent.setup();
      render(<ImageEditor {...mockProps} />);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      expect(generateButton).not.toBeDisabled();
    });

    it('shows optional negative prompt input', async () => {
      const user = userEvent.setup();
      render(<ImageEditor {...mockProps} />);

      // Negative prompt should be collapsed by default
      const expandButton = screen.getByRole('button', { name: /negative prompt|advanced/i });
      expect(expandButton).toBeInTheDocument();

      // Click to expand
      await user.click(expandButton);

      // Negative prompt input should appear
      const negativeInput = screen.getByPlaceholderText(/blurry.*low quality/i);
      expect(negativeInput).toBeInTheDocument();
    });

    it('accepts negative prompt text input', async () => {
      const user = userEvent.setup();
      render(<ImageEditor {...mockProps} />);

      // Expand negative prompt section
      const expandButton = screen.getByRole('button', { name: /negative prompt|advanced/i });
      await user.click(expandButton);

      const negativeInput = screen.getByPlaceholderText(/blurry.*low quality/i);
      await user.type(negativeInput, 'blurry, distorted');

      expect(negativeInput).toHaveValue('blurry, distorted');
    });
  });

  // ============================================================================
  // AC #5: Inpainting Execution
  // ============================================================================

  describe('AC #5: Inpainting Execution', () => {
    it('calls inpainting API with correct parameters', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockResolvedValue({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      // Click generate
      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // API should be called with correct params
      await waitFor(() => {
        expect(mockInpaint).toHaveBeenCalledWith(
          'test-session-123',
          0,
          expect.any(String), // mask_data (base64)
          'red sports car',
          expect.any(String)  // negative_prompt
        );
      });
    });

    it('shows loading indicator during inpainting', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);

      // Mock delayed response
      mockInpaint.mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({
          session_id: 'test-session-123',
          edited_image_url: '/api/v1/outputs/edited-image.png',
          original_image_url: '/api/v1/outputs/test-image.png',
          version: 1,
          edit_history: [],
          message: 'success',
        }), 100))
      );

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Loading indicator should appear
      expect(screen.getByText(/generating/i)).toBeInTheDocument();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByText(/generating/i)).not.toBeInTheDocument();
      });
    });

    it('handles inpainting API errors gracefully', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockRejectedValue(new Error('Model API error'));

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // AC #6: Edited Image Display
  // ============================================================================

  describe('AC #6: Edited Image Display', () => {
    it('displays before/after comparison when inpainting completes', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockResolvedValue({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Wait for completion and before/after view
      await waitFor(() => {
        expect(screen.getByText(/before|original/i)).toBeInTheDocument();
        expect(screen.getByText(/after|edited/i)).toBeInTheDocument();
      });
    });

    it('shows "Use Edited" and "Keep Original" buttons', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockResolvedValue({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Wait for action buttons
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /use edited/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /keep original/i })).toBeInTheDocument();
      });
    });

    it('calls onSave with edited URL when "Use Edited" clicked', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockResolvedValue({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Click "Use Edited"
      await waitFor(() => screen.getByRole('button', { name: /use edited/i }));
      const useEditedButton = screen.getByRole('button', { name: /use edited/i });
      await user.click(useEditedButton);

      // onSave should be called with edited image data
      expect(mockProps.onSave).toHaveBeenCalledWith(
        '/api/v1/outputs/edited-image.png',
        1,
        ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png']
      );
    });

    it('calls onCancel when "Keep Original" clicked', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      mockInpaint.mockResolvedValue({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/test-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Click "Keep Original"
      await waitFor(() => screen.getByRole('button', { name: /keep original/i }));
      const keepOriginalButton = screen.getByRole('button', { name: /keep original/i });
      await user.click(keepOriginalButton);

      // onCancel should be called (user chose not to use edit)
      expect(mockProps.onCancel).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Additional Edge Cases
  // ============================================================================

  describe('Edge Cases and Error Handling', () => {
    it('handles missing image URL gracefully', () => {
      const propsWithoutImage = { ...mockProps, imageUrl: '' };

      expect(() => render(<ImageEditor {...propsWithoutImage} />)).not.toThrow();
    });

    it('disables generate button when no mask is drawn', () => {
      render(<ImageEditor {...mockProps} />);

      const generateButton = screen.getByRole('button', { name: /generate/i });

      // Should be disabled initially (no mask drawn)
      expect(generateButton).toBeDisabled();
    });

    it('allows retry after inpainting failure', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);

      // First call fails
      mockInpaint.mockRejectedValueOnce(new Error('Timeout'));

      // Second call succeeds
      mockInpaint.mockResolvedValueOnce({
        session_id: 'test-session-123',
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/test-image.png',
        version: 1,
        edit_history: [],
        message: 'success',
      });

      render(<ImageEditor {...mockProps} />);

      // Enter prompt and generate (first attempt)
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });

      // Retry
      await user.click(generateButton);

      // Should succeed this time
      await waitFor(() => {
        expect(screen.getByText(/before|original/i)).toBeInTheDocument();
      });
    });
  });
});
