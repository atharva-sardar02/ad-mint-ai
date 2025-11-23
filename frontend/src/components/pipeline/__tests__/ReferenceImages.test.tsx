/**
 * Component tests for ReferenceImages component (Story 1.3)
 * Tests reference images display with GPT-4 Vision analysis
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReferenceImages } from "../ReferenceImages";
import type { ReferenceImage } from "../ReferenceImages";

describe("ReferenceImages Component", () => {
  it("should not render when images array is empty", () => {
    const { container } = render(<ReferenceImages images={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("should render banner message", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
      },
    ];

    render(<ReferenceImages images={images} />);
    expect(
      screen.getByText("Using these 3 reference images for visual consistency across all scenes")
    ).toBeInTheDocument();
  });

  it("should render custom display message when provided", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
      },
    ];

    render(
      <ReferenceImages
        images={images}
        displayMessage="Custom banner message"
      />
    );
    expect(screen.getByText("Custom banner message")).toBeInTheDocument();
  });

  it("should render reference images in grid", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
      },
      {
        url: "https://example.com/image2.jpg",
        type: "character",
      },
      {
        url: "https://example.com/image3.jpg",
        type: "environment",
      },
    ];

    render(<ReferenceImages images={images} />);

    const imageElements = screen.getAllByAltText(/Reference \d+/);
    expect(imageElements).toHaveLength(3);
  });

  it("should display image type labels", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
      },
    ];

    render(<ReferenceImages images={images} />);
    expect(screen.getByText("PRODUCT")).toBeInTheDocument();
  });

  it("should display GPT-4 Vision analysis summary when available", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
        analysis: {
          product_features: "Elegant bottle design",
          colors: ["#FF0000", "#00FF00"],
          style: "photorealistic",
          environment: "Indoor studio lighting",
        },
      },
    ];

    render(<ReferenceImages images={images} />);

    expect(screen.getByText("Visual Analysis Summary")).toBeInTheDocument();
    expect(screen.getByText(/Elegant bottle design/)).toBeInTheDocument();
    expect(screen.getByText(/photorealistic/)).toBeInTheDocument();
    expect(screen.getByText(/Indoor studio lighting/)).toBeInTheDocument();
  });

  it("should display character description when available", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "character",
        analysis: {
          character_description: "32-year-old woman with dark hair",
          colors: ["#000000"],
        },
      },
    ];

    render(<ReferenceImages images={images} />);

    expect(screen.getByText(/32-year-old woman with dark hair/)).toBeInTheDocument();
  });

  it("should not display analysis section when no analysis data", () => {
    const images: ReferenceImage[] = [
      {
        url: "https://example.com/image1.jpg",
        type: "product",
      },
    ];

    render(<ReferenceImages images={images} />);

    expect(screen.queryByText("Visual Analysis Summary")).not.toBeInTheDocument();
  });
});

