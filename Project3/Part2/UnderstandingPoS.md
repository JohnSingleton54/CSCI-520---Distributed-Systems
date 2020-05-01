# Understanding PoS Notes

R 4/30/2020

## 1. Creating the Blocks

> "Let verifiers (miners) create blocks in each time instance (say every 20 seconds) according to a probability _p_, instead of by mining."

One of the advantages of PoS is that blocks can be generated at a much faster rate. A rate that is often quoted is 1 block per 20 seconds (versus Bitcoin's 1 block per 10 minutes). The probability _p_ is equal to the validators' stake in the currency. I suggest that we initially give each of the four validators 1/4 of the (fixed) total number of coins that we want to circulate in our network. Maybe 25 each. Then, before the first block, each validator has _p_ = 1/4. So, each validator has a 25% chance of creating a candidate first block.

## 2. Deciding which block to take

> "Verifiers with a block interact through consensus to decide which one of them is allowed to add their block to the chain."

I think consensus will be achieved via a variation of the Follow The Satoshi Algorithm. Basically, this algorithm provides a way for there to be randomness whereby each validator has the same seed (something like the previous hash), and so either each validator can check the result of every other validators' coin tosses or each validator gets the same result as every other validator. Actually, I think we'll have to use this both for determining whether each validator will create a block and later for determining the winner.

## 3. Validating the chosen block

> "The winner contacts other verifiers, who sign the block, if the containing transactions do not contain double spending transactions (spender has money to spend) and if the block creator does not exceed _p_ in creating the block."

Well, in order to ensure that the block creator didn't exceed _p_ in creating the block, I'll think we'll have to do what I suggested in Step 2 and then have each validator check the results of the block creator's coin toss to make sure that it came up heads, and to check to make sure that the block creator was the winner.

## 4. Adding the chosen block

> "Once a block has signatures from enough verifiers, such that their stake exceeds the total of the transactions, the block can be added to the blockchain. Finally, a reward for the verifier that created the block and those who signed it is recorded in the block."

Suppose the first block consists of: Validator _A_ sends 20 coins to Validator _B_ (txn fee: 1 coin), and Validator _C_ sends 20 coins to Validator _D_ (txn fee: 1 coin). Validator _C_ won the right to create this block. His stake is 25 coins, which does not exceed the total of the transactions, which is 40 coins (or is it 42 coins?). Therefore at least one of the other validators will have to sign this block. I think we could allow for all of the validators to sign the block. (?) Anyway, the reward is 2 coins and is split 80-20 (or something like that) between the creator and the signers.

## 5. This solves two problems

> "This mechanism solves the “rich get richer” problem by assigning the reward to multiple miners that pool their stake. It also solves the “lazy miner” problem by making sure a block is generated before a verifier for the block is assigned."

Well, it at least partially solves the rich get richer problem in this way. As for the "lazy miner" problem, I think each block whose coin toss resulted in heads has to put forth a deposit of 1 coin or something like that. And if miner was chosen to be the block creator and didn't do his job, then he forfeits his deposit. (I think the coin gets slashed, in which case it's is marked and is basically taken out of circulation. Also, I think that the corresponding block becomes an empty block.)

## References

1. https://www.geeksforgeeks.org/proof-of-stake-pos-in-blockchain/

## Additional Notes

slashing - After a validator is selected, but before his stake is returned and his forging reward is
granted, the nodes on the network have to okay the block. If they find the block to be fraudulent,
then his forging reward is not granted and his stake is slashed (lost). (Where does his stake go?)

There will be a fixed number of coins circulating in the network.

An entity can gain coins either by receiving them in a txn or by forging a new block (assuming that
the block is okayed).

An entity can lose coins either by sending them in a txn, by txn fee, or by being slashed.

Q: Does an entity have to stake his entire amount of coins?
A: No. This is in Reference 1.
