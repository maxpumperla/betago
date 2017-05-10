## The principles behind super-human level computer Go
---

## Why?

- AlphaGo often talked about, but rarely how it works
- Learn to play go! |
- Disclaimer |

---

## Introduction to Go in one move

+++

<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/redmond_irritating.png">
</div>

+++
![redmond_irritating](https://www.youtube.com/embed/JNrXgpSEEIE?start=40&end=60)
<figure>
  <figcaption style="font-size: 16px;">https://www.youtube.com/embed/JNrXgpSEEIE</figcaption>
</figure>

+++
## What's so special?

##### "It’s not a human move. I’ve never seen a human play this move.”

- Thought to be a mistake at first
- Very creative & extremely unconventional |
- Opened new ways to think about the game |

---

## How can a machine learn patterns that were previously not considered by humans?

---

## Three pillars
- Tree search
- Supervised Learning |
- Reinforcement Learning |

---

## Tree search
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/chess-tree-search.png">
</div>
+++

## Some basics first

- Alternating two-player game
- Perfect information game |
- Zero-sum game |
- Markov property |
- There is an optimal value function $v^{\ast}(s)$ for each state $s$ |

+++
## Example: Evaluating Tic Tac Toe
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/tictactoe.png">
</div>

+++

## The perfect game of go (?)
- Evaluate all next moves
- Choose move maximizing your result|
- Opponent chooses move minimizing your result |
- Minimax |
- Discard hopeless sub-trees |
- Bound sub-trees by replacing them by $v^{\ast}(s)$ |
- Extension beat Kasparov in 1997 |

+++

## Well, but...
- Breadth $b \approx 250$, depth $d \approx 150$ |
- Completely intractable, $b^d$ moves |
- Sampling guesses and keeping track of outcome can work (MCTS) |
- "Randomly" playing out a full game is called rollout |
- Position evaluation in Go is extremely hard ($v^{\ast}(s)$?) |
- MCTS methods have been state of the art in Go for a long time |

---

## Supervised learning
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/policy_value_networks.png">
</div>
+++

## What can we hope to learn?
- What is my current position worth?
- Learn a good value function $v(s) \approx v^{\ast}(s)$ |
- What next move should I play? |
- Learn a good policy $p(a|s)$ |

+++

## Move prediction (classically)
- Feed an algorithm human game data
- For each $s$ predict the next move |
- Carefully hand-craft features (thousands of patterns)|
- exceeds capacity of humans and algorithms |

+++

## Enter Deep Learning
- Vastly successful in many applications
- Representation learning |
- Often no feature engineering |
- Special architectures |
- Note: bounded by data |

+++

## BetaGo - a python Go bot

- Currently supervised learning only, using [Keras](http://keras.io)
- Check it out on [github](https://github.com/maxpumperla/betago)
- Interactive demo available [here](https://betago.herokuapp.com)

---

## Reinforcement Learning
<div style="width: 70%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/reinforcement.jpg">
</div>

+++

## Terminology
- Have seen policies and value functions already |
- Know what states $s$ and actions $a$ are. |
- Can assign a reward function $r$: $+1$ for a win, $-1$ for a loss, otherwise $0$ |
- Outcome $z_t = \pm r(s_T)$ terminal reward at the end seen at $t$ |

+++

## How can we use this?
- Self-play
- Warm-start move prediction by supervised learning |
- Note: eventually supersedes data |

---
## AlphaGo: Combining approaches

+++

## How? Part I
- Policy network $p_{\sigma}$ from game data
- Initialize RL policy $p_{\rho}$ |
- Let $p_{\rho}$ play against older versions of itself |
- Train smaller policy net $p_{\pi}$ for fast rollouts |
- Updates using policy gradients $\Delta \rho \propto \frac{\partial log p_{\rho}(a_t | s_t)}{\partial \rho} z_t$ |

+++

## How? Part II
- Use state-outcome pairs $(s,z)$ from self-play to learn a value network $v_{\theta}(s)$ |
- Do this by regression, minimizing MSE between $v_{\theta}(s)$ and $z$, update by $\Delta \theta \propto \frac{\partial v_{\theta}(s)}{\partial \theta} (z - v(s))$ |
- Combine value network $v_{\theta}(s)$ and rollouts $z_L$ from fast policy as follows: |
- $V(s_L) = (1 - \lambda) v(s) + \lambda z_L$ |


---
## Conclusion
- All three pillars have been there before
- Very smart combination of these techniques |
- Incredible engineering achievement |
- At collectAI we are using DL and RL for communication: |
- when and how to contact a person |
