---
name: dspy
description: "DSPy: declarative LM programs, auto-optimize prompts, RAG."
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [dspy, openai, anthropic]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Prompt Engineering, DSPy, Declarative Programming, RAG, Agents, Prompt Optimization, LM Programming, Stanford NLP, Automatic Optimization, Modular AI]
    trigger_conditions:
      - "dspy"
      - "prompt optimization"
      - "declarative lm"
      - "auto-optimize prompts"
      - "dspy module"
      - "dspy signature"
      - "chain of thought dspy"
      - "rag pipeline"
      - "dspy optimizer"
      - "bootstrap fewshot"
      - "mipro optimization"
      - "dspy react agent"
---

# DSPy: Declarative Language Model Programming

## When to Use This Skill

Use DSPy when you need to:
- **Build complex AI systems** with multiple components and workflows
- **Program LMs declaratively** instead of manual prompt engineering
- **Optimize prompts automatically** using data-driven methods
- **Create modular AI pipelines** that are maintainable and portable
- **Improve model outputs systematically** with optimizers
- **Build RAG systems, agents, or classifiers** with better reliability

**GitHub Stars**: 22,000+ | **Created By**: Stanford NLP

## Not For

- Quick one-off prompts → use direct LLM calls
- Simple data extraction → use `instructor` (simpler API, less setup)
- When you have no training data → DSPy optimizers need examples to work
- Real-time streaming applications → DSPy is optimized for batch, not streaming
- When you need fine-grained control over prompt text → DSPy abstracts prompts away

## Pitfalls

1. **Not having training data for optimizers.** DSPy optimizers (BootstrapFewShot, MIPRO, etc.) require a `trainset` of `dspy.Example` objects. Without data, you can define signatures and modules but cannot optimize. Generate synthetic data or use a few representative examples.

2. **Forgetting to call `dspy.settings.configure(lm=lm)`.** Every DSPy program needs a configured LM. Without this, you'll get errors about no LM being set. Do this once at the start of your script.

3. **Using `dspy.Predict` when you need reasoning.** `dspy.Predict` does zero-shot prediction. For tasks requiring step-by-step reasoning, use `dspy.ChainOfThought` — it generates a `rationale` field automatically.

4. **Not setting `with_inputs()` on training examples.** When creating `dspy.Example` objects for the trainset, you must call `.with_inputs("field_name")` to specify which fields are inputs. Without this, the optimizer won't know what to vary.

5. **Over-optimizing on a small dataset.** Optimizers can overfit to a small trainset. Use at least 20-50 examples for meaningful optimization, and always evaluate on a separate test set.

6. **Not saving optimized modules.** Optimized modules lose their state when the process exits. Always save: `optimized.save("model.json")` and load: `loaded.load("model.json")`.

7. **Confusing signatures with modules.** Signatures define the I/O structure (what goes in, what comes out). Modules define the behavior (how to transform inputs to outputs). You need both.

8. **Using `dspy.ReAct` without defining tools properly.** Each tool function must have a clear docstring — DSPy uses the docstring as the tool description. Vague docstrings lead to poor tool selection.

9. **Not using `dspy.Assert` for critical invariants.** DSPy's assertion mechanism can catch and backtrack from invalid outputs. Use it for hard constraints that must be satisfied.

10. **Ignoring the trace.** DSPy stores every LM call in `dspy.settings.trace`. Use it for debugging: `for call in dspy.settings.trace: print(call['prompt'], call['response'])`.

11. **Using `dspy.OllamaLocal` without checking the base URL.** The default is `http://localhost:11434`. If Ollama runs on a different port or host, you must set `base_url` explicitly.

12. **Not setting `max_tokens` appropriately.** DSPy's ChainOfThought generates reasoning steps before the answer. If `max_tokens` is too low, the reasoning gets truncated and the answer is garbage. Use at least 1000 for CoT.

## Installation

```bash
# Stable release
pip install dspy

# Latest development version
pip install git+https://github.com/stanfordnlp/dspy.git

# With specific LM providers
pip install dspy[openai]        # OpenAI
pip install dspy[anthropic]     # Anthropic Claude
pip install dspy[all]           # All providers
```

## Quick Start

### Basic Example: Question Answering

```python
import dspy

# Configure your language model
lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Define a signature (input → output)
class QA(dspy.Signature):
    """Answer questions with short factual answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

# Create a module
qa = dspy.Predict(QA)

# Use it
response = qa(question="What is the capital of France?")
print(response.answer)  # "Paris"
```

### Chain of Thought Reasoning

```python
import dspy

lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Use ChainOfThought for better reasoning
class MathProblem(dspy.Signature):
    """Solve math word problems."""
    problem = dspy.InputField()
    answer = dspy.OutputField(desc="numerical answer")

# ChainOfThought generates reasoning steps automatically
cot = dspy.ChainOfThought(MathProblem)

response = cot(problem="If John has 5 apples and gives 2 to Mary, how many does he have?")
print(response.rationale)  # Shows reasoning steps
print(response.answer)     # "3"
```

## Core Concepts

### 1. Signatures

Signatures define the structure of your AI task (inputs → outputs):

```python
# Inline signature (simple)
qa = dspy.Predict("question -> answer")

# Class signature (detailed)
class Summarize(dspy.Signature):
    """Summarize text into key points."""
    text = dspy.InputField()
    summary = dspy.OutputField(desc="bullet points, 3-5 items")

summarizer = dspy.ChainOfThought(Summarize)
```

**When to use each:**
- **Inline**: Quick prototyping, simple tasks
- **Class**: Complex tasks, type hints, better documentation

### 2. Modules

Modules are reusable components that transform inputs to outputs:

#### dspy.Predict
Basic prediction module:

```python
predictor = dspy.Predict("context, question -> answer")
result = predictor(context="Paris is the capital of France",
                   question="What is the capital?")
```

#### dspy.ChainOfThought
Generates reasoning steps before answering:

```python
cot = dspy.ChainOfThought("question -> answer")
result = cot(question="Why is the sky blue?")
print(result.rationale)  # Reasoning steps
print(result.answer)     # Final answer
```

#### dspy.ReAct
Agent-like reasoning with tools:

```python
from dspy.predict import ReAct

class SearchQA(dspy.Signature):
    """Answer questions using search."""
    question = dspy.InputField()
    answer = dspy.OutputField()

def search_tool(query: str) -> str:
    """Search Wikipedia."""
    # Your search implementation
    return results

react = ReAct(SearchQA, tools=[search_tool])
result = react(question="When was Python created?")
```

#### dspy.ProgramOfThought
Generates and executes code for reasoning:

```python
pot = dspy.ProgramOfThought("question -> answer")
result = pot(question="What is 15% of 240?")
# Generates: answer = 240 * 0.15
```

### 3. Optimizers

Optimizers improve your modules automatically using training data:

#### BootstrapFewShot
Learns from examples:

```python
from dspy.teleprompt import BootstrapFewShot

# Training data
trainset = [
    dspy.Example(question="What is 2+2?", answer="4").with_inputs("question"),
    dspy.Example(question="What is 3+5?", answer="8").with_inputs("question"),
]

# Define metric
def validate_answer(example, pred, trace=None):
    return example.answer == pred.answer

# Optimize
optimizer = BootstrapFewShot(metric=validate_answer, max_bootstrapped_demos=3)
optimized_qa = optimizer.compile(qa, trainset=trainset)

# Now optimized_qa performs better!
```

#### MIPRO (Most Important Prompt Optimization)
Iteratively improves prompts:

```python
from dspy.teleprompt import MIPRO

optimizer = MIPRO(
    metric=validate_answer,
    num_candidates=10,
    init_temperature=1.0
)

optimized_cot = optimizer.compile(
    cot,
    trainset=trainset,
    num_trials=100
)
```

#### BootstrapFinetune
Creates datasets for model fine-tuning:

```python
from dspy.teleprompt import BootstrapFinetune

optimizer = BootstrapFinetune(metric=validate_answer)
optimized_module = optimizer.compile(qa, trainset=trainset)

# Exports training data for fine-tuning
```

### 4. Building Complex Systems

#### Multi-Stage Pipeline

```python
import dspy

class MultiHopQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=3)
        self.generate_query = dspy.ChainOfThought("question -> search_query")
        self.generate_answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        # Stage 1: Generate search query
        search_query = self.generate_query(question=question).search_query

        # Stage 2: Retrieve context
        passages = self.retrieve(search_query).passages
        context = "\n".join(passages)

        # Stage 3: Generate answer
        answer = self.generate_answer(context=context, question=question).answer
        return dspy.Prediction(answer=answer, context=context)

# Use the pipeline
qa_system = MultiHopQA()
result = qa_system(question="Who wrote the book that inspired the movie Blade Runner?")
```

#### RAG System with Optimization

```python
import dspy
from dspy.retrieve.chromadb_rm import ChromadbRM

# Configure retriever
retriever = ChromadbRM(
    collection_name="documents",
    persist_directory="./chroma_db"
)

class RAG(dspy.Module):
    def __init__(self, num_passages=3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)

# Create and optimize
rag = RAG()

# Optimize with training data
from dspy.teleprompt import BootstrapFewShot

optimizer = BootstrapFewShot(metric=validate_answer)
optimized_rag = optimizer.compile(rag, trainset=trainset)
```

## LM Provider Configuration

### Anthropic Claude

```python
import dspy

lm = dspy.Claude(
    model="claude-sonnet-4-5-20250929",
    api_key="your-api-key",  # Or set ANTHROPIC_API_KEY env var
    max_tokens=1000,
    temperature=0.7
)
dspy.settings.configure(lm=lm)
```

### OpenAI

```python
lm = dspy.OpenAI(
    model="gpt-4",
    api_key="your-api-key",
    max_tokens=1000
)
dspy.settings.configure(lm=lm)
```

### Local Models (Ollama)

```python
lm = dspy.OllamaLocal(
    model="llama3.1",
    base_url="http://localhost:11434"
)
dspy.settings.configure(lm=lm)
```

### Multiple Models

```python
# Different models for different tasks
cheap_lm = dspy.OpenAI(model="gpt-3.5-turbo")
strong_lm = dspy.Claude(model="claude-sonnet-4-5-20250929")

# Use cheap model for retrieval, strong model for reasoning
with dspy.settings.context(lm=cheap_lm):
    context = retriever(question)

with dspy.settings.context(lm=strong_lm):
    answer = generator(context=context, question=question)
```

## Common Patterns

### Pattern 1: Structured Output

```python
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")
    occupation: str = Field(description="Current job")

class ExtractPerson(dspy.Signature):
    """Extract person information from text."""
    text = dspy.InputField()
    person: PersonInfo = dspy.OutputField()

extractor = dspy.TypedPredictor(ExtractPerson)
result = extractor(text="John Doe is a 35-year-old software engineer.")
print(result.person.name)  # "John Doe"
print(result.person.age)   # 35
```

### Pattern 2: Assertion-Driven Optimization

```python
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler

class MathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.solve = dspy.ChainOfThought("problem -> solution: float")

    def forward(self, problem):
        solution = self.solve(problem=problem).solution

        # Assert solution is numeric
        dspy.Assert(
            isinstance(float(solution), float),
            "Solution must be a number",
            backtrack=backtrack_handler
        )

        return dspy.Prediction(solution=solution)
```

### Pattern 3: Self-Consistency

```python
import dspy
from collections import Counter

class ConsistentQA(dspy.Module):
    def __init__(self, num_samples=5):
        super().__init__()
        self.qa = dspy.ChainOfThought("question -> answer")
        self.num_samples = num_samples

    def forward(self, question):
        # Generate multiple answers
        answers = []
        for _ in range(self.num_samples):
            result = self.qa(question=question)
            answers.append(result.answer)

        # Return most common answer
        most_common = Counter(answers).most_common(1)[0][0]
        return dspy.Prediction(answer=most_common)
```

### Pattern 4: Retrieval with Reranking

```python
class RerankedRAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=10)
        self.rerank = dspy.Predict("question, passage -> relevance_score: float")
        self.answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        # Retrieve candidates
        passages = self.retrieve(question).passages

        # Rerank passages
        scored = []
        for passage in passages:
            score = float(self.rerank(question=question, passage=passage).relevance_score)
            scored.append((score, passage))

        # Take top 3
        top_passages = [p for _, p in sorted(scored, reverse=True)[:3]]
        context = "\n\n".join(top_passages)

        # Generate answer
        return self.answer(context=context, question=question)
```

## Evaluation and Metrics

### Custom Metrics

```python
def exact_match(example, pred, trace=None):
    """Exact match metric."""
    return example.answer.lower() == pred.answer.lower()

def f1_score(example, pred, trace=None):
    """F1 score for text overlap."""
    pred_tokens = set(pred.answer.lower().split())
    gold_tokens = set(example.answer.lower().split())

    if not pred_tokens:
        return 0.0

    precision = len(pred_tokens & gold_tokens) / len(pred_tokens)
    recall = len(pred_tokens & gold_tokens) / len(gold_tokens)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)
```

### Evaluation

```python
from dspy.evaluate import Evaluate

# Create evaluator
evaluator = Evaluate(
    devset=testset,
    metric=exact_match,
    num_threads=4,
    display_progress=True
)

# Evaluate model
score = evaluator(qa_system)
print(f"Accuracy: {score}")

# Compare optimized vs unoptimized
score_before = evaluator(qa)
score_after = evaluator(optimized_qa)
print(f"Improvement: {score_after - score_before:.2%}")
```

## Best Practices

### 1. Start Simple, Iterate

```python
# Start with Predict
qa = dspy.Predict("question -> answer")

# Add reasoning if needed
qa = dspy.ChainOfThought("question -> answer")

# Add optimization when you have data
optimized_qa = optimizer.compile(qa, trainset=data)
```

### 2. Use Descriptive Signatures

```python
# ❌ Bad: Vague
class Task(dspy.Signature):
    input = dspy.InputField()
    output = dspy.OutputField()

# ✅ Good: Descriptive
class SummarizeArticle(dspy.Signature):
    """Summarize news articles into 3-5 key points."""
    article = dspy.InputField(desc="full article text")
    summary = dspy.OutputField(desc="bullet points, 3-5 items")
```

### 3. Optimize with Representative Data

```python
# Create diverse training examples
trainset = [
    dspy.Example(question="factual", answer="...").with_inputs("question"),
    dspy.Example(question="reasoning", answer="...").with_inputs("question"),
    dspy.Example(question="calculation", answer="...").with_inputs("question"),
]

# Use validation set for metric
def metric(example, pred, trace=None):
    return example.answer in pred.answer
```

### 4. Save and Load Optimized Models

```python
# Save
optimized_qa.save("models/qa_v1.json")

# Load
loaded_qa = dspy.ChainOfThought("question -> answer")
loaded_qa.load("models/qa_v1.json")
```

### 5. Monitor and Debug

```python
# Enable tracing
dspy.settings.configure(lm=lm, trace=[])

# Run prediction
result = qa(question="...")

# Inspect trace
for call in dspy.settings.trace:
    print(f"Prompt: {call['prompt']}")
    print(f"Response: {call['response']}")
```

## Comparison to Other Approaches

| Feature | Manual Prompting | LangChain | DSPy |
|---------|-----------------|-----------|------|
| Prompt Engineering | Manual | Manual | Automatic |
| Optimization | Trial & error | None | Data-driven |
| Modularity | Low | Medium | High |
| Type Safety | No | Limited | Yes (Signatures) |
| Portability | Low | Medium | High |
| Learning Curve | Low | Medium | Medium-High |

**When to choose DSPy:**
- You have training data or can generate it
- You need systematic prompt improvement
- You're building complex multi-stage systems
- You want to optimize across different LMs

**When to choose alternatives:**
- Quick prototypes (manual prompting)
- Simple chains with existing tools (LangChain)
- Custom optimization logic needed

## Resources

- **Documentation**: https://dspy.ai
- **GitHub**: https://github.com/stanfordnlp/dspy (22k+ stars)
- **Discord**: https://discord.gg/XCGy2WDCQB
- **Twitter**: @DSPyOSS
- **Paper**: "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines"

## See Also

- `references/modules.md` - Detailed module guide (Predict, ChainOfThought, ReAct, ProgramOfThought)
- `references/optimizers.md` - Optimization algorithms (BootstrapFewShot, MIPRO, BootstrapFinetune)
- `references/examples.md` - Real-world examples (RAG, agents, classifiers)
