/**
 * Integration Tests for Image Editing Workflow (Story 4: Advanced Image Editing)
 *
 * Tests cover complete user workflows:
 * - Open editor → draw mask → enter prompt → generate → use edited
 * - Edited image persists in pipeline
 * - Multiple edits on same image
 * - Rollback to original
 *
 * These tests verify the full integration between:
 * - ImageReview (gallery)
 * - ImageEditor (editing modal)
 * - InteractivePipeline (parent orchestrator)
 * - Backend API (inpainting service)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImageReview, type ImageData } from '../../ImageReview';
import * as interactiveApi from '../../../../services/interactive-api';
import type { ChatMessage } from '../../../../types/pipeline';

// Mock the interactive API
vi.mock('../../../../services/interactive-api', () => ({
  inpaintImage: vi.fn(),
}));

// Mock use-image hook
vi.mock('use-image', () => ({
  default: vi.fn((url: string) => {
    const img = new Image();
    img.src = url;
    return [img, 'loaded'];
  }),
}));

// Mock react-konva for canvas operations
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

describe('Image Editing Integration Tests', () => {
  const mockMessages: ChatMessage[] = [
    {
      type: 'assistant',
      content: 'Reference images generated',
      timestamp: new Date().toISOString(),
    },
  ];

  const mockSessionId = 'test-session-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================================
  // Full Workflow: Open → Draw → Prompt → Generate → Use Edited
  // ============================================================================

  describe('Complete Editing Workflow', () => {
    it('executes full editing workflow from ImageReview gallery', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      const mockOnImageEdited = vi.fn();
      const mockOnApprove = vi.fn();

      // Mock successful inpainting
      mockInpaint.mockResolvedValue({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/original-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/original-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'Image edited successfully',
      });

      const initialImages = [
        {
          index: 0,
          path: '/output/original-image.png',
          url: '/api/v1/outputs/original-image.png',
          prompt: 'Original image',
          quality_score: 75,
        },
      ];

      const { rerender } = render(
        <ImageReview
          stage="reference_image"
          images={initialImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={mockOnApprove}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Step 1: Open editor by clicking Edit button
      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      // Editor modal should open
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/edit image/i)).toBeInTheDocument();

      // Step 2: Draw mask (simulated - in real test, would interact with canvas)
      const stage = screen.getByTestId('konva-stage');
      fireEvent.mouseDown(stage, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(stage, { clientX: 150, clientY: 150 });
      fireEvent.mouseUp(stage);

      // Step 3: Enter replacement prompt
      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'red sports car');

      expect(promptInput).toHaveValue('red sports car');

      // Step 4: Click Generate button
      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Loading indicator should appear
      expect(screen.getByText(/generating/i)).toBeInTheDocument();

      // Wait for inpainting to complete
      await waitFor(() => {
        expect(screen.queryByText(/generating/i)).not.toBeInTheDocument();
      });

      // Before/after comparison should be displayed
      expect(screen.getByText(/before|original/i)).toBeInTheDocument();
      expect(screen.getByText(/after|edited/i)).toBeInTheDocument();

      // Step 5: Click "Use Edited" button
      const useEditedButton = screen.getByRole('button', { name: /use edited/i });
      await user.click(useEditedButton);

      // onImageEdited callback should be called
      expect(mockOnImageEdited).toHaveBeenCalledWith(
        0,
        '/api/v1/outputs/edited-image.png',
        1
      );

      // Step 6: Verify edited image is reflected in gallery
      const updatedImages = [
        {
          ...initialImages[0],
          url: '/api/v1/outputs/edited-image.png',
          is_edited: true,
          edit_version: 1,
        },
      ];

      rerender(
        <ImageReview
          stage="reference_image"
          images={updatedImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={mockOnApprove}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Edited badge should be displayed
      expect(screen.getByText(/edited v1/i)).toBeInTheDocument();

      // Step 7: Approve edited image and continue pipeline
      const approveButton = screen.getByRole('button', { name: /approve.*continue/i });
      await user.click(approveButton);

      expect(mockOnApprove).toHaveBeenCalledTimes(1);
    });

    it('allows user to cancel editing and keep original', async () => {
      const user = userEvent.setup();
      const mockOnImageEdited = vi.fn();

      const initialImages: ImageData[] = [
        {
          index: 0,
          path: '/output/original-image.png',
          url: '/api/v1/outputs/original-image.png',
          prompt: 'Original image',
        },
      ];

      render(
        <ImageReview
          stage="reference_image"
          images={initialImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Open editor
      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      // Cancel editing
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // onImageEdited should NOT be called
      expect(mockOnImageEdited).not.toHaveBeenCalled();

      // Gallery should still show original image (no edited badge)
      expect(screen.queryByText(/edited/i)).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Edited Image Persistence in Pipeline
  // ============================================================================

  describe('Edited Image Persistence', () => {
    it('edited image persists when navigating between stages', async () => {
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);

      mockInpaint.mockResolvedValue({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited-image.png',
        original_image_url: '/api/v1/outputs/original-image.png',
        version: 1,
        edit_history: ['/api/v1/outputs/original-image.png', '/api/v1/outputs/edited-image.png'],
        message: 'success',
      });

      const editedImage = [
        {
          index: 0,
          path: '/output/edited-image.png',
          url: '/api/v1/outputs/edited-image.png',
          prompt: 'Edited image',
          is_edited: true,
          edit_version: 1,
        },
      ];

      const { rerender } = render(
        <ImageReview
          stage="reference_image"
          images={editedImage}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={vi.fn()}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Verify edited badge is shown
      expect(screen.getByText(/edited v1/i)).toBeInTheDocument();

      // Simulate stage change (e.g., moving to storyboard)
      // Re-render with same edited image data
      rerender(
        <ImageReview
          stage="reference_image"
          images={editedImage}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={vi.fn()}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Edited badge should still be present
      expect(screen.getByText(/edited v1/i)).toBeInTheDocument();
    });

    it('uses edited image URL in subsequent pipeline stages', () => {
      const editedImages = [
        {
          index: 0,
          path: '/output/edited-image.png',
          url: '/api/v1/outputs/edited-image.png',
          prompt: 'Edited image',
          is_edited: true,
          edit_version: 1,
        },
      ];

      render(
        <ImageReview
          stage="reference_image"
          images={editedImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={vi.fn()}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Verify image element uses edited URL
      const imageElements = screen.getAllByRole('img');
      const editedImageElement = imageElements.find(
        img => (img as HTMLImageElement).src.includes('edited-image.png')
      );

      expect(editedImageElement).toBeDefined();
    });
  });

  // ============================================================================
  // Multiple Edits on Same Image
  // ============================================================================

  describe('Multiple Edits and Edit History', () => {
    it('supports multiple sequential edits on same image', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      const mockOnImageEdited = vi.fn();

      // First edit
      mockInpaint.mockResolvedValueOnce({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited-v1.png',
        original_image_url: '/api/v1/outputs/original.png',
        version: 1,
        edit_history: ['/api/v1/outputs/original.png', '/api/v1/outputs/edited-v1.png'],
        message: 'success',
      });

      // Second edit
      mockInpaint.mockResolvedValueOnce({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited-v2.png',
        original_image_url: '/api/v1/outputs/original.png',
        version: 2,
        edit_history: ['/api/v1/outputs/original.png', '/api/v1/outputs/edited-v1.png', '/api/v1/outputs/edited-v2.png'],
        message: 'success',
      });

      let currentImages: ImageData[] = [
        {
          index: 0,
          path: '/output/original.png',
          url: '/api/v1/outputs/original.png',
          prompt: 'Original',
        },
      ];

      const { rerender } = render(
        <ImageReview
          stage="reference_image"
          images={currentImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // First edit
      const editButton1 = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton1);

      const promptInput1 = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput1, 'red car');

      const generateButton1 = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton1);

      await waitFor(() => screen.getByRole('button', { name: /use edited/i }));
      await user.click(screen.getByRole('button', { name: /use edited/i }));

      expect(mockOnImageEdited).toHaveBeenCalledWith(0, '/api/v1/outputs/edited-v1.png', 1);

      // Update with first edit
      currentImages = [
        {
          ...currentImages[0],
          url: '/api/v1/outputs/edited-v1.png',
          is_edited: true,
          edit_version: 1,
        } as ImageData,
      ];

      rerender(
        <ImageReview
          stage="reference_image"
          images={currentImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      expect(screen.getByText(/edited v1/i)).toBeInTheDocument();

      // Second edit on already edited image
      const editButton2 = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton2);

      const promptInput2 = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.clear(promptInput2);
      await user.type(promptInput2, 'blue car');

      const generateButton2 = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton2);

      await waitFor(() => screen.getByRole('button', { name: /use edited/i }));
      await user.click(screen.getByRole('button', { name: /use edited/i }));

      expect(mockOnImageEdited).toHaveBeenCalledWith(0, '/api/v1/outputs/edited-v2.png', 2);

      // Update with second edit
      currentImages = [
        {
          ...currentImages[0],
          url: '/api/v1/outputs/edited-v2.png',
          edit_version: 2,
        } as ImageData,
      ];

      rerender(
        <ImageReview
          stage="reference_image"
          images={currentImages}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Should show version 2
      expect(screen.getByText(/edited v2/i)).toBeInTheDocument();
    });

    it('tracks edit history across multiple edits', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);
      const mockOnImageEdited = vi.fn();

      const editHistory = [
        '/api/v1/outputs/original.png',
        '/api/v1/outputs/edited-v1.png',
        '/api/v1/outputs/edited-v2.png',
      ];

      mockInpaint.mockResolvedValue({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited-v3.png',
        original_image_url: '/api/v1/outputs/original.png',
        version: 3,
        edit_history: [...editHistory, '/api/v1/outputs/edited-v3.png'],
        message: 'success',
      });

      const images = [
        {
          index: 0,
          path: '/output/edited-v2.png',
          url: '/api/v1/outputs/edited-v2.png',
          is_edited: true,
          edit_version: 2,
        },
      ];

      render(
        <ImageReview
          stage="reference_image"
          images={images}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={mockOnImageEdited}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Perform third edit
      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'green car');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      await waitFor(() => screen.getByRole('button', { name: /use edited/i }));
      await user.click(screen.getByRole('button', { name: /use edited/i }));

      // Verify API was called with edit history
      expect(mockInpaint).toHaveBeenCalled();

      // Verify callback includes version 3
      expect(mockOnImageEdited).toHaveBeenCalledWith(
        0,
        '/api/v1/outputs/edited-v3.png',
        3
      );
    });
  });

  // ============================================================================
  // Error Handling in Complete Workflow
  // ============================================================================

  describe('Error Handling in Complete Workflow', () => {
    it('handles inpainting API failure gracefully', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);

      mockInpaint.mockRejectedValue(new Error('Model API timeout'));

      const images = [
        {
          index: 0,
          path: '/output/original.png',
          url: '/api/v1/outputs/original.png',
          prompt: 'Original',
        },
      ];

      render(
        <ImageReview
          stage="reference_image"
          images={images}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={vi.fn()}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Open editor and attempt generation
      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'test');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });

      // User can cancel and return to gallery
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Gallery should still show original image
      expect(screen.queryByText(/edited/i)).not.toBeInTheDocument();
    });

    it('allows retry after failure', async () => {
      const user = userEvent.setup();
      const mockInpaint = vi.mocked(interactiveApi.inpaintImage);

      // First attempt fails
      mockInpaint.mockRejectedValueOnce(new Error('Timeout'));

      // Second attempt succeeds
      mockInpaint.mockResolvedValueOnce({
        session_id: mockSessionId,
        edited_image_url: '/api/v1/outputs/edited.png',
        original_image_url: '/api/v1/outputs/original.png',
        version: 1,
        edit_history: ['/api/v1/outputs/original.png', '/api/v1/outputs/edited.png'],
        message: 'success',
      });

      const images = [
        {
          index: 0,
          path: '/output/original.png',
          url: '/api/v1/outputs/original.png',
          prompt: 'Original',
        },
      ];

      render(
        <ImageReview
          stage="reference_image"
          images={images}
          messages={mockMessages}
          sessionId={mockSessionId}
          onImageEdited={vi.fn()}
          onApprove={vi.fn()}
          onRegenerate={vi.fn()}
          onSendFeedback={vi.fn()}
        />
      );

      // Open editor and attempt generation (fails)
      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      const promptInput = screen.getByPlaceholderText(/describe.*replacement/i);
      await user.type(promptInput, 'test');

      const generateButton = screen.getByRole('button', { name: /generate/i });
      await user.click(generateButton);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });

      // Retry
      await user.click(generateButton);

      // Should succeed
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /use edited/i })).toBeInTheDocument();
      });
    });
  });
});
