## The principles behind super-human level computer Go
---

## Why?

- Google's AlphaGo was announced 2016
- Advancement 10+ years ahead of its time |
- Often talked about, but rarely how it works |
- Few lessons to be learnt |
- The game itself is beautiful |
- Disclaimer: Think of chess or Tic Tac Toe if you like |

---

## Introduction to Go in two moves

+++

## Ear-reddening move
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/ear_reddening.png">
</div>

+++

<!-- - Shusaku vs. Inseki, game 2 (1846) -->
- Among the most famous moves in history
- Move "feels right" |
- There are many local patterns to respect |
- Complex interaction with surrounding stones |
- Value depends on exact board position |
- Hard to evaluate the position itself |

+++

## AlphaGo - Lee Sedol
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/redmond_irritating.png">
</div>

+++

<iframe width="420" height="315"
src="https://www.youtube.com/watch?v=JNrXgpSEEIE?autoplay=1&start=40&end=60&version=3">
</iframe>

+++

- Very creative move by the computer
- Went against conventional wisdom |
- Unlikely to be played by professionals |
- Was initially thought to be a mistake by the machine |
- Opened new ways to think about the game |

---

## How can a machine learn patterns that were previously not considered by humans?

---

## Three pillars
- Tree search
- Supervised Learning
- Reinforcement Learning

---

## Tree search
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/chess-tree-search.png">
</div>
+++

## Some basics first

- Players take turns (alternating two-player game)
- No luck involved (perfect information game) |
- What's good for me is bad for you (zero-sum) |
- The current position is all that counts, no matter how I ended up there (Markov property) |
- There is an optimal value function $v^{\ast}(s)$ for each position/state $s$ |
- We call this an alternating Markov game |

+++
## Example: Evaluating Tic Tac Toe
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/tictactoe.png">
</div>

+++

## The perfect game of go (?)
- Evaluate all next moves (search the tree)
- Choose the move that maximizes your result (likely win) |
- Your opponent will choose the move that minimizes your result (likely loss) |
- This tree search approach is called minimax |
- Discard hopeless sub-trees |
- Bound sub-trees by replacing them by $v^{\ast}(s)$ |
- A sophisticated extension of this beat Kasparov in 1997 (alpha-beta pruning) |

+++

## Well, but...
- breadth $b \approx 250$, depth $d \approx 150$ |
- A game has about $b^d$ moves, completely intractable |
- Sampling guesses and keeping track of outcome can work (MCTS) |
- "Randomly" playing out a full game is called rollout |
- Position evaluation in Go is extremely hard ($v^{\ast}(s)$?) |
- MCTS methods have been state of the art in Go for a long time |

---

## Supervised learning

+++

## What can we hope to learn?
- What is my current position worth?
- Learn a good value function $v(s) \approx v^{\ast}(s)$ |
- What next move should I play? |
- Learn a good policy $P(a|s)$ |

+++

## Move prediction (classically)
- Feed an algorithm human game data
- For each board position, learn to predict the next move |
- Need to carefully hand-craft features from raw data |
- There's thousands of patterns to detect |
- exceeds capacity of humans (feature engineering) and shallow algorithms (logistic regression, SVMs etc.) |

+++

## Enter Deep Learning
- Deep neural networks have been vastly successful in many applications
- Really good at detecting hierarchical patterns/features (representation learning) |
- Can often feed raw data, no feature engineering needed |
- Convolutional networks particularly good at learning from spatial data |
- Note: will never be better than data |

+++

## AlphaGo's supervised Deep Learning
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/policy_value_networks.png">
</div>

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
- Know what states $s$ and actions $a$ are.
- Can assign a reward function $r$: $+1$ for a win, $-1$ for a loss, otherwise $0$ |
- Have seen policies and value functions already |

+++

## How can we use this?
- Self-play: two agents playing against each other and learn
- Can "warm start" move prediction by supervised learning |
- Can eventually supersede approach learning from historical data |

---
## AlphaGo: Combining approaches

+++

## How? High level
- Learn a policy network from game data (move prediction)
- Use this network as starting point for self-play |
- Let computer play against other versions of itself |
- Massive improvement already |
- Use this better network to derive a value network (position evaluation) |
- Do tree search. Choose move by considering: |
  - value function |
  - sampling rollouts using our policy network |

+++

## How? Expert slide I
- policy $p_{\sigma}$ computed by 13-layer conv net with ReLU activations
- Use this to initialize RL policy $p_{\rho}$ |
- also learn a smaller policy net $p_{\pi}$ for fast rollouts |
- Outcome $z_t = \pm r(s_T)$ terminal reward at the end seen at $t<T$ |
- Updates using policy gradients $\Delta \rho \propto \frac{\partial log p_{\rho}(a_t | s_t)}{\partial \rho} z_t$ |
- Use state-outcome pairs $(s,z)$ from self-play to learn a value network $v_{\theta}(s)$ |

+++

## How? Expert slide II
- Do this by regression, minimizing MSE between $v_{\theta}(s)$ and $z$
- i.e. updates given by $\Delta \theta \propto \frac{\partial v_{\theta}(s)}{\partial \theta} (z - v(s))$ |
- Combine value network $v_{\theta}(s)$ and rollouts $z_L$ from fast policy as follows: |
- $V(s_L) = (1 - \lambda) v(s) + \lambda z_L$ |

+++
<div style="width: 70%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/sl_to_rl.png">
</div>


---
## Conclusion
- All three pillars have been there before
- AlphaGo represents a very smart combination of these techniques |
- Incredible engineering achievement |
- Techniques can be transferred |
- At collectAI we are using DL and RL for debtor communication: |
  - find right time to contact a person |
  - in which tone to address a person |
  - on which channel etc. |

---
## Bonus slides

+++
## Elo comparison
<div style="width: 70%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/elo_comparison.png">
</div>

+++
## AlphaGo performance
<div style="width: 70%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/alphago_performance.png">
</div>

+++
