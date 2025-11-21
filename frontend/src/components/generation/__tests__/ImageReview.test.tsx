/**
 * Tests for ImageReview Component
 *
 * Tests cover:
 * - Gallery rendering
 * - Image selection (single and multi-select)
 * - Approve/regenerate actions
 * - Quality score display
 * - Story 4: Edit button integration (AC #7-8)
 * - Story 4: ImageEditor modal opening
 * - Story 4: Edited badge display
 * - Story 4: Edit history tracking
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImageReview } from '../ImageReview';
import type { ChatMessage } from '../../../types/pipeline';

// Mock ImageEditor component
vi.mock('../ImageEditor', () => ({
  default: vi.fn(({ onSave, onCancel }) => (
    <div data-testid="image-editor-modal">
      <button onClick={() => onSave('/edited-url.png', 1, ['/original.png', '/edited-url.png'])}>
        Mock Save
      </button>
      <button onClick={onCancel}>Mock Cancel</button>
    </div>
  )),
}));

describe('ImageReview', () => {
  const mockMessages: ChatMessage[] = [
    {
      type: 'assistant',
      content: 'I generated 3 reference images',
      timestamp: new Date().toISOString(),
    },
  ];

  const mockImages = [
    {
      index: 1,
      path: '/output/image_1.png',
      url: '/api/v1/outputs/image_1.png',
      prompt: 'Test prompt 1',
      quality_score: 85,
    },
    {
      index: 2,
      path: '/output/image_2.png',
      url: '/api/v1/outputs/image_2.png',
      prompt: 'Test prompt 2',
      quality_score: 72,
    },
  ];

  const mockHandlers = {
    onSendFeedback: vi.fn(),
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
  };

  it('renders reference image gallery', () => {
    render(
      <ImageReview
        stage="reference_image"
        images={mockImages}
        messages={mockMessages}
        {...mockHandlers}
      />
    );

    expect(screen.getByText(/Reference Images/i)).toBeInTheDocument();
    expect(screen.getByText(/Image 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Image 2/i)).toBeInTheDocument();
  });

  it('displays quality scores', () => {
    render(
      <ImageReview
        stage="reference_image"
        images={mockImages}
        messages={mockMessages}
        {...mockHandlers}
      />
    );

    expect(screen.getByText(/85\/100/i)).toBeInTheDocument();
    expect(screen.getByText(/72\/100/i)).toBeInTheDocument();
  });

  it('allows image selection', () => {
    render(
      <ImageReview
        stage="reference_image"
        images={mockImages}
        messages={mockMessages}
        {...mockHandlers}
      />
    );

    const firstImage = screen.getAllByRole('button')[0];
    fireEvent.click(firstImage);

    expect(screen.getByText(/1 selected/i)).toBeInTheDocument();
  });

  it('calls onApprove when approve button clicked', () => {
    render(
      <ImageReview
        stage="reference_image"
        images={mockImages}
        messages={mockMessages}
        {...mockHandlers}
      />
    );

    const approveButton = screen.getByText(/Approve & Continue/i);
    fireEvent.click(approveButton);

    expect(mockHandlers.onApprove).toHaveBeenCalledTimes(1);
  });

  // ============================================================================
  // Story 4: Image Editing Integration Tests (AC #7-8)
  // ============================================================================

  describe('Story 4: Image Editing Integration', () => {
    const mockSessionId = 'test-session-123';
    const mockOnImageEdited = vi.fn();

    const mockImagesForEdit = [
      {
        index: 0,
        path: '/output/image_0.png',
        url: '/api/v1/outputs/image_0.png',
        prompt: 'Test image',
        quality_score: 80,
      },
    ];

    beforeEach(() => {
      vi.clearAllMocks();
    });

    // AC #7: Integration with Pipeline
    describe('AC #7: Edit Button and Integration', () => {
      it('shows Edit button on image hover when sessionId is provided', () => {
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Edit button should be rendered (though may be hidden by hover CSS)
        expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      });

      it('does NOT show Edit button when sessionId is missing', () => {
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            {...mockHandlers}
          />
        );

        // Edit button should not be present without sessionId
        expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
      });

      it('opens ImageEditor modal when Edit button is clicked', async () => {
        const user = userEvent.setup();
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        // ImageEditor modal should be rendered
        expect(screen.getByTestId('image-editor-modal')).toBeInTheDocument();
      });

      it('closes ImageEditor modal when cancel is clicked', async () => {
        const user = userEvent.setup();
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Open editor
        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        // Cancel editing
        const cancelButton = screen.getByRole('button', { name: /mock cancel/i });
        await user.click(cancelButton);

        // Modal should be closed
        expect(screen.queryByTestId('image-editor-modal')).not.toBeInTheDocument();
      });

      it('calls onImageEdited when edited image is saved', async () => {
        const user = userEvent.setup();
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Open editor
        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        // Save edited image
        const saveButton = screen.getByRole('button', { name: /mock save/i });
        await user.click(saveButton);

        // onImageEdited should be called with correct params
        expect(mockOnImageEdited).toHaveBeenCalledWith(
          0, // imageIndex
          '/edited-url.png', // editedUrl
          1 // version
        );

        // Modal should be closed after save
        expect(screen.queryByTestId('image-editor-modal')).not.toBeInTheDocument();
      });

      it('updates gallery with edited image URL after save', async () => {
        const user = userEvent.setup();

        // Use a stateful component to simulate URL update
        const { rerender } = render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Open editor and save
        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        const saveButton = screen.getByRole('button', { name: /mock save/i });
        await user.click(saveButton);

        // Simulate parent component updating image URL
        const updatedImages = [
          {
            ...mockImagesForEdit[0],
            url: '/edited-url.png',
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
            {...mockHandlers}
          />
        );

        // Image should now show edited badge
        expect(screen.getByText(/edited v1/i)).toBeInTheDocument();
      });
    });

    // AC #8: Multiple Edits and Edit History
    describe('AC #8: Multiple Edits and Edit History', () => {
      it('displays "Edited" badge on modified images', () => {
        const editedImage = [
          {
            index: 0,
            path: '/output/image_0.png',
            url: '/api/v1/outputs/edited_v1.png',
            prompt: 'Test image',
            quality_score: 80,
            is_edited: true,
            edit_version: 1,
          },
        ];

        render(
          <ImageReview
            stage="reference_image"
            images={editedImage}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Edited badge should be displayed
        expect(screen.getByText(/edited v1/i)).toBeInTheDocument();
      });

      it('shows correct version number in badge for multiple edits', () => {
        const multiEditedImage = [
          {
            index: 0,
            path: '/output/image_0.png',
            url: '/api/v1/outputs/edited_v3.png',
            prompt: 'Test image',
            quality_score: 80,
            is_edited: true,
            edit_version: 3,
          },
        ];

        render(
          <ImageReview
            stage="reference_image"
            images={multiEditedImage}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Badge should show version 3
        expect(screen.getByText(/edited v3/i)).toBeInTheDocument();
      });

      it('allows editing an already edited image (edit on edit)', async () => {
        const user = userEvent.setup();
        const editedImage = [
          {
            index: 0,
            path: '/output/image_0.png',
            url: '/api/v1/outputs/edited_v1.png',
            prompt: 'Test image',
            quality_score: 80,
            is_edited: true,
            edit_version: 1,
          },
        ];

        render(
          <ImageReview
            stage="reference_image"
            images={editedImage}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Click edit button on edited image
        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        // ImageEditor should open with edited image
        expect(screen.getByTestId('image-editor-modal')).toBeInTheDocument();
      });

      it('passes correct imageId to ImageEditor for tracking', async () => {
        const user = userEvent.setup();
        const images = [
          {
            index: 0,
            path: '/output/image_0.png',
            url: '/api/v1/outputs/image_0.png',
            prompt: 'Image 1',
          },
          {
            index: 1,
            path: '/output/image_1.png',
            url: '/api/v1/outputs/image_1.png',
            prompt: 'Image 2',
          },
        ];

        render(
          <ImageReview
            stage="reference_image"
            images={images}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Click edit on second image
        const editButtons = screen.getAllByRole('button', { name: /edit/i });
        await user.click(editButtons[1]);

        // Save and verify correct imageId is passed to callback
        const saveButton = screen.getByRole('button', { name: /mock save/i });
        await user.click(saveButton);

        expect(mockOnImageEdited).toHaveBeenCalledWith(
          1, // imageId should be 1 (second image)
          expect.any(String),
          expect.any(Number)
        );
      });
    });

    // Edge Cases
    describe('Edit Integration Edge Cases', () => {
      it('handles missing onImageEdited callback gracefully', async () => {
        const user = userEvent.setup();
        render(
          <ImageReview
            stage="reference_image"
            images={mockImagesForEdit}
            messages={mockMessages}
            sessionId={mockSessionId}
            // onImageEdited intentionally omitted
            {...mockHandlers}
          />
        );

        const editButton = screen.getByRole('button', { name: /edit/i });
        await user.click(editButton);

        const saveButton = screen.getByRole('button', { name: /mock save/i });

        // Should not throw error
        expect(() => fireEvent.click(saveButton)).not.toThrow();
      });

      it('does not interfere with image selection when editing', async () => {
        const user = userEvent.setup();
        const multipleImages = [
          {
            index: 0,
            path: '/output/image_0.png',
            url: '/api/v1/outputs/image_0.png',
            prompt: 'Image 1',
          },
          {
            index: 1,
            path: '/output/image_1.png',
            url: '/api/v1/outputs/image_1.png',
            prompt: 'Image 2',
          },
        ];

        render(
          <ImageReview
            stage="reference_image"
            images={multipleImages}
            messages={mockMessages}
            sessionId={mockSessionId}
            onImageEdited={mockOnImageEdited}
            {...mockHandlers}
          />
        );

        // Select first image by clicking on the card (not the edit button)
        const imageCards = screen.getAllByRole('button').filter(
          btn => !btn.textContent?.includes('Edit')
        );
        await user.click(imageCards[0]);

        // Selection should work
        expect(screen.getByText(/1 selected/i)).toBeInTheDocument();
      });
    });
  });

  // TODO: Add more comprehensive tests
  // - Storyboard clip rendering
  // - Multi-select functionality
  // - Feedback sending with selected indices
  // - Regenerate with/without selection
  // - Chat interface integration
});
