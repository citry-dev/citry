import { type ReactNode, useContext } from "react";
import { BoardContext } from "./board-context";

type CardProps = {
  title: string;
  count: number;
  tone: "plain" | "accent";
  // The card hands its title and count back, and the page builds the footer.
  footer: (card: { title: string; count: number }) => ReactNode;
  onHide: () => void;
};

export default function Card({ title, count, tone, footer, onHide }: CardProps) {
  // The page provides the board's name to every card.
  const boardName = useContext(BoardContext);
  return (
    <div className={`card card--${tone}`}>
      <p>
        {title}: {count} tasks
      </p>
      <p>Board: {boardName}</p>
      <div className="card-footer">{footer({ title, count })}</div>
      <button type="button" onClick={onHide}>
        Hide
      </button>
    </div>
  );
}
