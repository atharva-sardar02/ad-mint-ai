/**
 * ReferenceImages Component
 *
 * Displays reference images inline in chat feed with GPT-4 Vision analysis.
 * Read-only display per Story 1.2 constraint (no feedback/regeneration in MVP).
 */


export interface ReferenceImage {
  url: string;
  type: string;
  analysis?: {
    character_description?: string;
    product_features?: string;
    colors: string[];
    style?: string;
    environment?: string;
  };
}

export interface ReferenceImagesProps {
  /** Array of reference images */
  images: ReferenceImage[];
  /** Display message/banner text */
  displayMessage?: string;
  /** CSS class name */
  className?: string;
}

export function ReferenceImages({
  images,
  displayMessage = "Using these 3 reference images for visual consistency across all scenes",
  className = "",
}: ReferenceImagesProps) {
  if (images.length === 0) {
    return null;
  }

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}>
      {/* Banner Message */}
      <div className="mb-4">
        <p className="text-sm font-semibold text-blue-900">{displayMessage}</p>
      </div>

      {/* Image Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {images.map((image, index) => (
          <div key={index} className="relative">
            <img
              src={image.url}
              alt={`Reference ${index + 1} (${image.type})`}
              className="w-full h-48 object-cover rounded-lg border border-gray-300"
            />
            <div className="mt-2">
              <span className="text-xs font-semibold text-gray-600 uppercase">
                {image.type}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* GPT-4 Vision Analysis Summary */}
      {images.some((img) => img.analysis) && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            Visual Analysis Summary
          </h4>
          <div className="space-y-2 text-sm text-gray-700">
            {images.map((image, index) => {
              if (!image.analysis) return null;

              const { analysis } = image;
              return (
                <div key={index} className="bg-white rounded p-3">
                  <div className="font-semibold text-gray-900 mb-1">
                    {image.type.charAt(0).toUpperCase() + image.type.slice(1)} Image
                  </div>
                  {analysis.character_description && (
                    <div className="mb-1">
                      <span className="font-medium">Character: </span>
                      <span>{analysis.character_description}</span>
                    </div>
                  )}
                  {analysis.product_features && (
                    <div className="mb-1">
                      <span className="font-medium">Product: </span>
                      <span>{analysis.product_features}</span>
                    </div>
                  )}
                  {analysis.colors && analysis.colors.length > 0 && (
                    <div className="mb-1">
                      <span className="font-medium">Colors: </span>
                      <span>{analysis.colors.join(", ")}</span>
                    </div>
                  )}
                  {analysis.style && (
                    <div className="mb-1">
                      <span className="font-medium">Style: </span>
                      <span>{analysis.style}</span>
                    </div>
                  )}
                  {analysis.environment && (
                    <div>
                      <span className="font-medium">Environment: </span>
                      <span>{analysis.environment}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

