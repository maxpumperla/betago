## The principles behind super-human level computer Go
---

## Why?

- Google's AlphaGo was announced 2016
- Often talked about, but rarely how it works |
- Few lessons to be learnt |
- The game itself is beautiful |
- Disclaimer: Think of chess or Tic Tac Toe if you like

---

<!-- ### Introduction to Go in two moves
### Tree search
### Supervised Learning
### Reinforcement Learning
### AlphaGo: combining all
### betago demo
### Conclusion

--- -->

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

- Very creative move by the computer
- Went against conventional wisdom |
- Unlikely to be played by professionals |
- Was initially thought to be a mistake by the machine

---

## How can a machine learn patterns that were previously not considered by humans?

---

## Three pillars
- Tree search
- Supervised Learning
- Reinforcement Learning

---

## Tree search

+++

## Some basics first

- Players take turns (alternating two-player game)
- No luck involved (perfect information game) |
- What's good for me is bad for you (zero-sum) |
- The current position is all that counts, no matter how I ended up there (Markov property) |
- There is an optimal _value function_ $v^{\ast}(s)$ for each position/state $s$ |
- We call this an alternating Markov game |

+++
## Example: Evaluating Tic Tac Toe
<div style="width: 50%; display: inline-block">
    <img src="https://raw.githubusercontent.com/maxpumperla/betago/hamburg-ai/tictactoe.png">
</div>

+++

## The perfect game of go (?)
- In current position, evaluate all next moves (search the tree)
- Choose the move that maximizes your result (likely win) |
- Your opponent will choose the move that minimizes your result (likely loss) |
- This tree search approach is called _minimax_ |
- Discard hopeless sub-trees |
- Bound sub-trees by replacing them by $v^{\ast}(s)$ |
- A sophisticated extension of this beat Kasparov in 1997 (alpha-beta pruning) |
+++

## Well, but...
- breadth $b \approx 250$, depth $d \approx 150$ |
- A game has about $b^d$ moves, completely intractable |
- Sampling guesses and keeping track of outcome can work (MCTS) |
- Position evaluation in Go is extremely hard ($v^{\ast}(s)$?) |
- MCTS methods have been state of the art in Go for a long time |

---

## Supervised learning

+++

## What can we hope to learn?
- What is my current position worth?
- Learn a good _value function_ $v(s) \approx v^{\ast}(s)$ |
- What next move should I play? |
- Learn a good _policy_ $P(a|s)$ |

+++

---
### Vanity slide


---
### Company slide
