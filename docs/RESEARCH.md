# My Research Operating System

We run exploratory research to understand AI through an empirical, hypothesis-driven approach. 
Research isn't linear, it's a graph search over a hypothesis space.

Each **Research** is modeled as a State DAG (Directed Acyclic Graph):
* **Nodes:** States of knowledge. At initialization, we define the **Initial State** and **Goal State**.
* **Edges:** Transitions between states produced by a set of experiments.


# Research Architecture
```
[ Research Question ]  <-- see context/research_questions/

|
V

[ Testable Hypothesis ] <-- see context/experiment_runs/

|
V

[ Single Run ] <-- Executed via configs/ and logged in outputs/

|
V

[ State Update / Repeat ] <-- update context/ and repeat

```


# Research Execution Loop
### Research Phase (Macro Loop)
1. **Define Goal:** Understand the objective and establish measurable target metrics.
2. **Establish Baseline:** Review context and establish the naive baseline.
3. **Map State DAG:** Identify the current node position within the search space.
4. **Quantify Delta:** Measure the exact gap between current baseline metrics and the goal state.
5. **Formulate Question:** Frame the primary research question driving the next transition.

### Experiment Phase (Hypothesis Design)
6. **Design Hypothesis:** Construct a testable hypothesis changing **one variable at a time**.

### Run Execution Phase (Micro Loop)
7. **Execute & Capture:** Run the experiment config and record the run artifact:  
    ```
    Artifact = {Run ID, Git Commit Hash, Parent Commit Hash, Metrics, Result Output}

    where, `Git Commit Hash` captures {Dataset, Prompt, Config}
    ```
8. **Analyze Result:** Evaluate quantitative scores alongside qualitative error.
9. **Update DAG Context:**
    * **On Success:** Add a new state node and advance the branch.
    * **On Failure / Dead End:** Mark edge as invalidated, log negative results, and backtrack to parent node.

10. **Traverse Search Space:** Repeat experimental phase (step 6 to 9) until the the hypothesis branch is fully exhausted or goal is reached.
