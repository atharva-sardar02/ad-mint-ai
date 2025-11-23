/**
 * QuickActions Component
 *
 * Approve/regenerate buttons for interactive checkpoints.
 * Shown at story and scene stages per PRD FR57-FR63/FR29-FR31.
 */


export interface QuickActionsProps {
  /** Callback when user approves */
  onApprove: () => void;
  /** Callback when user requests regeneration */
  onRegenerate: () => void;
  /** Whether regeneration is in progress */
  isRegenerating?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
}

export function QuickActions({
  onApprove,
  onRegenerate,
  isRegenerating = false,
  disabled = false,
  className = "",
}: QuickActionsProps) {
  return (
    <div className={`flex gap-3 ${className}`}>
      <button
        onClick={onRegenerate}
        disabled={disabled || isRegenerating}
        className="flex-1 px-4 py-2 bg-yellow-500 text-white font-semibold rounded-lg hover:bg-yellow-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isRegenerating ? "Regenerating..." : "Regenerate"}
      </button>
      <button
        onClick={onApprove}
        disabled={disabled || isRegenerating}
        className="flex-1 px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        ✓ Approve & Continue
      </button>
    </div>
  );
}

