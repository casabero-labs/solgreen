import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "./App";

afterEach(() => {
  cleanup();
  document.documentElement.dataset.theme = "light";
});

describe("Solgreen unified frontend", () => {
  it("identifies demo data and avoids presenting it as a real plant", () => {
    render(<App />);

    expect(screen.getByText("Datos demostrativos")).toBeInTheDocument();
    expect(screen.getByText(/No representa una planta real/i)).toBeInTheDocument();
  });

  it("updates dashboard metrics when the period changes", () => {
    render(<App />);

    expect(screen.getByTestId("production-value")).toHaveTextContent("28.4 kWh");
    fireEvent.click(screen.getByRole("button", { name: "7d" }));
    expect(screen.getByTestId("production-value")).toHaveTextContent("191.6 kWh");
  });

  it("blocks current monetary claims without a verified tariff profile", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Economía" }));
    expect(screen.getByText("Resultado monetario bloqueado")).toBeInTheDocument();
    expect(screen.getByText("No se muestra COP actual")).toBeInTheDocument();
  });

  it("supports a global dark mode toggle", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Activar modo oscuro" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByRole("button", { name: "Activar modo claro" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
