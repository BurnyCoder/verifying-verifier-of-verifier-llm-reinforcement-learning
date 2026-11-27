"""Compare how exact arithmetic and assigned rewards evolve on each solver's own sampled answers."""

from .records import terminal
from .tables import markdown


def training_quarters(rollouts):
    """Partition complete four-sample updates in order and cross-tabulate rewards against exact labels."""
    updates = len(rollouts) // 4
    windows = []
    for quarter in range(4):
        begin, end = (updates * quarter) // 4, (updates * (quarter + 1)) // 4
        samples = rollouts[4 * begin:4 * end]
        if not samples:
            continue
        right = [row for row in samples if row["label"]]
        wrong = [row for row in samples if not row["label"]]
        windows.append(dict(first_update=begin+1, last_update=end, n=len(samples), correct=len(right),
                            rewarded_correct=sum(row["reward"] for row in right),
                            rewarded_wrong=sum(row["reward"] for row in wrong),
                            j2_rewarded_correct=sum(terminal(row["reports"][1], 2) for row in right),
                            j2_rewarded_wrong=sum(terminal(row["reports"][1], 2) for row in wrong)))
    return windows


def quarter_rows(review):
    """Pair time windows from separate policies on the same scheduled questions."""
    for shallow, deep in zip(review["two"]["quarters"], review["three"]["quarters"], strict=True):
        span = f"{shallow['first_update']}–{shallow['last_update']}"
        row = [span]
        for window in (shallow, deep):
            row.extend([f"{window['correct']}/{window['n']}", window["rewarded_correct"], window["rewarded_wrong"]])
        yield row


def quarter_table(review):
    return markdown(["Updates", "J2-trained solver correct", "J2 paid correct", "J2 paid wrong",
                     "J3-trained solver correct", "J3 paid correct", "J3 paid wrong"], list(quarter_rows(review)))


def late_rewards(review):
    """Put the previous judge on the very same late answers to distinguish reward quality from answer mix."""
    last = review["three"]["quarters"][-1]
    correct, wrong = last["correct"], last["n"]-last["correct"]
    return (f"In the last quarter Judge 3 rewarded **{last['rewarded_correct']}/{correct} correct attempts** and "
            f"**{last['rewarded_wrong']}/{wrong} wrong attempts**. On these identical late answers, Judge 2 would "
            f"have rewarded {last['j2_rewarded_correct']}/{correct} correct attempts and {last['j2_rewarded_wrong']}/"
            f"{wrong} wrong ones. Both grades depend on which answers the evolving solver produces. These "
            "trajectories establish when the gap appeared. The contributions of individual updates and seed "
            "variation remain distinct questions.")


def save_trajectory_figure(review, target):
    """Show the same fractions and time windows for the two solvers with a common vertical scale."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(9.0, 3.65), constrained_layout=True)
    for ax, arm, title in zip(axes, ("two", "three"), ("Trained with two judges", "Trained with three judges"), strict=True):
        windows = review[arm]["quarters"]
        x = [w["last_update"] for w in windows]
        ax.plot(x, [w["correct"]/w["n"] for w in windows], marker="o", color="#B65127", label="Exactly correct")
        ax.plot(x, [(w["rewarded_correct"]+w["rewarded_wrong"])/w["n"] for w in windows], marker="s",
                color="#1E5260", linestyle="--", label="Awarded reward")
        ax.set(ylim=(0, 1), yticks=[0, .25, .5, .75, 1], xticks=x, xlabel="Last update in quarter", title=title)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Share of sampled answers")
    axes[1].legend(loc="upper right", frameon=False, fontsize=9)
    fig.suptitle(f"Arithmetic and reward over training · seed {review['seed']}")
    fig.savefig(target, dpi=150)
    plt.close(fig)
