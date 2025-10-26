import type { UploadHint } from "../types/jobs";

type ProcessStepsProps = {
  hints: UploadHint[];
  activeIndex: number;
  onSelect: (index: number) => void;
};

export function ProcessSteps({ hints, activeIndex, onSelect }: ProcessStepsProps) {
  return (
    <section className="panel">
      <h2>核心流程</h2>
      <ul>
        {hints.map((hint, index) => (
          <li key={hint.title}>
            <button
              className={index === activeIndex ? "step active" : "step"}
              type="button"
              onClick={() => onSelect(index)}
            >
              <span className="step-index">{index + 1}</span>
              <span>
                <strong>{hint.title}</strong>
                <br />
                <small>{hint.description}</small>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
