import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders login screen", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: /doctor sign in/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
});
