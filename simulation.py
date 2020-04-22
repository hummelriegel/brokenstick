import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

if __name__ == '__main__':
    runs = 100
    iterations = 10_000

    breakpoints_dfs = []
    diffs_dfs = []
    triangles_dfs = []

    for run in range(runs):
        breakpoints = np.random.uniform(0, 1, (iterations, 2))
        breakpoints_sorted = np.sort(breakpoints, axis=1)
        lower_limit = np.zeros((iterations, 1))
        upper_limit = np.ones((iterations, 1))
        points = np.concatenate((lower_limit, breakpoints_sorted, upper_limit), axis=1)
        diffs = np.diff(points, axis=1)

        # Check for triangles
        diffs_ok = (diffs < 0.5).all(axis=1)  # no part is longer than 0.5
        # the max part is not longer than the two smaller ones together (should be the same result anyway)
        max_diff_ok = np.amax(diffs, axis=1) < (diffs.sum(axis=1) - np.amax(diffs, axis=1))

        triangles = np.logical_and(diffs_ok, max_diff_ok)

        # First Result
        print(
            f"Run {run + 1:04}: {sum(triangles)} triangles in {iterations:,} iterations."
            f"That equals a probability of {sum(triangles) / iterations}."
        )

        # Check Distributions
        breakpoints_df = pd.DataFrame(breakpoints_sorted, columns=["lower_break", "higher_break"])
        breakpoints_df.index.name = 'iteration'
        breakpoints_df.reset_index(inplace=True)
        breakpoints_df.iteration = breakpoints_df.iteration + 1
        breakpoints_df["run"] = run + 1
        breakpoints_dfs.append(breakpoints_df)

        diffs_df = pd.DataFrame(diffs, columns=['diff_lower_bound', 'diff_between', 'diff_upper_bound'])
        diffs_df.index.name = 'iteration'
        diffs_df.reset_index(inplace=True)
        diffs_df.iteration = diffs_df.iteration + 1
        diffs_df["run"] = run + 1
        diffs_dfs.append(diffs_df)

        triangles_df = pd.DataFrame(triangles, columns=["is_triangle"])
        triangles_df.index.name = 'iteration'
        triangles_df.reset_index(inplace=True)
        triangles_df.iteration = triangles_df.iteration + 1
        triangles_df["run"] = run + 1
        triangles_df['cumsum_abs'] = triangles_df.is_triangle.cumsum()
        triangles_df['cumsum_rel'] = triangles_df.cumsum_abs / (triangles_df.iteration + 1)
        triangles_dfs.append(triangles_df)

    breakpoints_dfs = pd.concat(breakpoints_dfs)
    diffs_dfs = pd.concat(diffs_dfs)
    triangles_dfs = pd.concat(triangles_dfs)

    print(triangles_dfs.columns)
    print(diffs_dfs.columns)
    print(breakpoints_dfs.columns)

    max_cumsum_rel = triangles_dfs[triangles_dfs.iteration == triangles_dfs.iteration.max()].loc[:, 'cumsum_rel']
    triangle_mean = np.mean(max_cumsum_rel)
    triangle_std = np.std(max_cumsum_rel)

    # Create Figures
    # https://dev.to/pj_trainor/better-plots-in-three-lines-2eb7
    # https://hackaday.com/2019/03/07/make-xkcd-style-plots-from-python/
    # https://matplotlib.org/3.1.1/tutorials/text/text_intro.html

    title = f"Probablilty of a Triangle: {triangle_mean:.2f}$\pm${triangle_std:.2f}\n"\
            f"after {runs:,} simulation runs with {iterations:,} iterations each"
    print(title)

    figure_iterations = [100, 1_000, 10_000]
    number_of_rows = len(figure_iterations)

    fig, ax = plt.subplots(nrows=number_of_rows, ncols=3, figsize=(15, 3 * number_of_rows))
    plt.subplots_adjust(wspace=0.4, hspace=0.5)
    fig.suptitle(title)

    for row, max_iteration in enumerate(figure_iterations):
        # Plot Triangles
        data_triangles = triangles_dfs[triangles_dfs.iteration <= max_iteration]

        ax_next = ax[row, 0]
        ax_next.set_title(f"{max_iteration:,} Iterations")

        lns1 = sns.lineplot(x='iteration', y='cumsum_abs', data=data_triangles, ax=ax_next, label="Absolute",
                            estimator='mean', legend=False)
        ax_next.set(xlabel='Iteration', ylabel='Count of triangles')

        ax_next_twin = ax_next.twinx()
        lns2 = sns.lineplot(x='iteration', y='cumsum_rel', data=data_triangles, ax=ax_next_twin, color='r',
                            label="Relative", estimator='mean', legend=False)
        ax_next_twin.set(ylabel='Percentage of triangles [%]')
        ax_next_twin.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

        lns = lns1.lines + lns2.lines
        labs = [l.get_label() for l in lns]
        ax_next.legend(lns, labs, loc=0)

        # Plot Distribution of Breakpoints
        data_breakpoints = breakpoints_dfs[breakpoints_dfs.iteration <= max_iteration]
        data_breakpoints = list(data_breakpoints.lower_break) + list(data_breakpoints.higher_break)

        ax_next = ax[row, 1]
        sns.distplot(data_breakpoints, bins=10, ax=ax_next)
        ax_next.set(xlabel='Position of breaks on original stick [% of original length]', ylabel='Density [%]')
        ax_next.set_xlim(0, 1)

        # Plot Distribution of Stick Lengths
        data_diffs = diffs_dfs[breakpoints_dfs.iteration <= max_iteration]
        data_diffs = list(data_diffs.diff_lower_bound) + list(data_diffs.diff_between) + list(
            data_diffs.diff_upper_bound)

        ax_next = ax[row, 2]
        sns.distplot(data_diffs, bins=10, ax=ax_next)
        ax_next.set(xlabel='Length of resulting sticks after breaking [% of original length]',
                    ylabel='Density [%]')
        ax_next.set_xlim(0, 1)

    fig.savefig(f"img/simulation_default.png", dpi=360)
