import type { ReactNode } from "react";

type CardProps = {
  title: string;
  count: number;
  tone: "plain" | "accent";
  // The card hands its title and count back, and the page builds the footer.
  footer: (card: { title: string; count: number }) => ReactNode;
  onHide: () => void;
};

export default function Card({ title, count, tone, footer, onHide }: CardProps) {
  return (
    <div className={`card card--${tone}`}>
      <p>
        {title}: {count} tasks
      </p>
      <div className="card-footer">{footer({ title, count })}</div>
      <button type="button" onClick={onHide}>
        Hide
      </button>
    </div>
  );
}
