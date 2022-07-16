import * as React from "react";
import { render } from "@testing-library/react";
import App from "../components/App";

describe("App component", () => {

  it("renders the elements correctly", async () => {
    const { container } = render(
      <App />
    );

    expect(container.querySelectorAll(".app")).toHaveLength(1);
    expect(container.querySelectorAll(".app-container")).toHaveLength(1);
   });
});
