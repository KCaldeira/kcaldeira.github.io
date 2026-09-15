---
layout: post
title: "Voting analysis for the 19th Chopin Competition"
date: 2025-11-12T20:04:25+00:00
slug: chopin-voting-analysis
wp_id: 2435
---

{% include figure.html src="/assets/images/2025/11/image.jpg" alt="n an absurd waste of time, I wrote a blog post about voting and the 19th Chopin Competition. There has been controversy about who should have won. Different voting systems would yield different winners. Differences in top rankings are statistically insignificant." link="https://bsky.app/profile/kencaldeira.com/post/3m5iegf7ouc2p" %}

[Ben Laude](https://benlaude.com) made [a YouTube video](https://youtu.be/AzsruBUVdfA?si=3u6su-_yDBY_7I5V) in which he interviewed Eugene Chan about his [analysis of the voting of the 2025 19th Chopin Competition](https://euge.ca/chopin-2025).

I have thought a little about voting systems and [the judges scores were made available on the Competition Web site](https://www.chopincompetition.pl/en/newsroom/19th-chopin-competition-judges-scores?id=144&type=news), so I thought why not create some python code to analyze who the winners of the 19th competition under voting systems that were not used by the actual competition.

The [github repository containing the processing code](https://github.com/KCaldeira/chopin_voting), [input data files](https://github.com/KCaldeira/chopin_voting/tree/main/data/input), and [results](https://github.com/KCaldeira/chopin_voting/tree/main/data/output), for all of the analysis described here is freely available. Feel free to copy it and modify it to perform your own preferred analyses.

\[Since the original publication of this blog post, it has come to my attention that there is a another analysis of Chopin Competition voting at [https://euge.ca/chopin-2025](https://euge.ca/chopin-2025).\]

## VOTING SYSTEMS

Before discussing voting systems, it is useful to take note of Nobel Prize Winner [Kenneth Arrow’s impossibility theorem](https://en.wikipedia.org/wiki/Arrow%27s_impossibility_theorem). I’ll let you look into it on your own, but it shows mathematically that there is no perfect voting system, that every voting system has its flaws.

This motivates my attempt to use several reasonable voting systems. If several reasonable voting systems yield the same winner, then it is likely the best winner was chosen.

\[Incidentally, I was able to participate in some seminars at Stanford in which Kenneth Arrow also participated. I feel very fortunate that, in my life, I have gotten to meet, or at least be in the room with. some towering giants of accomplishment.\]

In all of the voting systems considered, I take the numerical scores of each judge and then use the scores to rank the preferences across the different contestants. If two contestants receive the same score, it is assumed the judge has no preference between the two of them.

## “First past the post” : Most first choices

There is a voting system often known as “[First past the post](https://en.wikipedia.org/wiki/First-past-the-post_voting)“.

In this voting system, whoever gets the most first choice votes wins. If a judge had two people rated as first choice, that would count as 1/2 a vote for each.

Then the person receiving the most first choice votes wins (assuming there is no tie, and there was not). That person is then removed from everyone’s list, and the process is repeated to determine the second place winner, and so on to the bottom of the list.

## “Copeland’s method”: Most wins on pairwise comparisons

[Copeland’s method](https://en.wikipedia.org/wiki/Copeland%27s_method) is to take the judges’ ratings of the contestants, and compare how they would be judged by each judge in a pairwise comparison, and then take the person who would do best in the most pair-wise competition.

One point is added to each contestant’s score for winning a pairwise competition as judged independently by each judge, and a point is subtracted from each contestant’s score for losing a pairwise competition. A tie neither adds nor subtracts points.

The person who has the highest point score then wins.

If there is one person who is preferred over everybody else by over half the judges, this is known as a [Condorcet winner](https://en.wikipedia.org/wiki/Condorcet_winner_criterion). It may not be obvious that someone can score highest on Copeland’s method without being a Condorcet winner, but it is possible. In fact, this happened in the first round of this year’s competition.

## “Instant Runoff Voting”: Top-down elimination

In [instant runoff voting,](https://en.wikipedia.org/wiki/Instant-runoff_voting) the candidate with fewest first preference votes is eliminated, and everyone who had that candidate as a first choice now has that candidate eliminated from their ranking so now their second choice is their first choice.

This process is iterated until some candidate gets a majority of the votes.

To determine the second place winner, the first place winner is removed from every judge’s ranking and the process is repeated. To get the third place winner, we remove the first and second place winners and repeat the process and so on.

## Bottom-elimination voting

Bottom-elimination voting is the same as instant runoff voting except the process starts from the bottom instead of the top.

It is essentially repeating instant runoff voting where you flip everyone’s ranking so that the judges’ last choices are at the top and their first choices are at the bottom, and then you see who got to the lowest rankings, etc.

If instant runoff voting tries to find the candidate liked by the greatest number of judges, bottom elimination voting tries to find the candidate disliked by the fewest number of judges.

## THE RESULTS

The results of this exercise can be found in an excel file located [here](https://github.com/KCaldeira/chopin_voting/tree/main/data/output).

## Stage 1

In Stage 1, with 84 contestants, the following five contestants got the highest scores on each of the voting systems:

_Table 1:  Stage 1 voting results_

| Rank | FIrst past the post | COPELAND’s Method | INSTANT RUNOFF VOTING | BOTTOM ELIMINATION VOTING | COMPETITION METHOD |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Kevin Chen | Kevin Chen | Kevin Chen | Kevin Chen | **Kevin Chen** |
| 2 | Eric Guo | Eric Guo | Xiaoyu Hu | Eric Guo | **Eric Guo** |
| 3 | Vincent Ong | Taianyao Lyu | Eric Guo | Eric Lu | **Vincent Ong** |
| 4 | Piotr Pawlak | Miyu Shindu | Vincent Ong | Miyu Shindo | **Tianyao Lyu** |
| 5 | Hao Rao | Shiori Kuwahara | Hao Rao | Tianyao Lyu | **Shiori Kuwahara** |

The first thing to notice is that all of these voting systems agree that Kevin Chen won the first round. Four out of the five methods agree that Eric Guo placed second.  There is reasonable cause for argument about the remaining places.

Further note that 4 out of the people top-ranked by Copeland’s method appear in the same order as chosen in the Competition. Thus it seems the Competition method is closest to Copeland’s method.

Each of these voting systems have different implications for who would be one of the 40 contestants to pass on to Stage 2.

Under the first past the post system, there were 14 people who would have passed to Stage 2 but did not (and 14 people who did pass to Stage 2 but would not have). You can look at the linked excel file to look at names.

Under Copeland’s method, there were only 2 people who would or would not have passed to Stage 2, compared to who was actually chosen to continue to Stage 2.  For the instant runoff voting, there was a discrepancy of 5 people either way, and for the bottom elimination method, the discrepancy was 6 people.

By this criterion also, the Competition method seems closest to Copeland’s method.

## Stage 2

In Stage 2, of the 40 contestants competing, the following five contestants got the highest scores on each of the voting systems:

_Table 2:  Stage 2 voting results_

| Rank | FIrst past the post | COPELAND’s Method | INSTANT RUNOFF VOTING | BOTTOM ELIMINATION VOTING | COMPETITION METHOD |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | William Yang | Eric Lu | Eric Lu | Eric Lu | **Eric Lu** |
| 2 | Kevin Chen | Kevin Chen | Kevin Chen | Kevin Chen | **Kevin Chen** |
| 3 | Tomoharu Ushida | William Yang | William Yang | David Khrikuli | **William Yang** |
| 4 | Eric Lu | Tianyou Li | Tomoharu Ushida | Shiori Kuwahara | ****Shiori Kuwahara**** |
| 5 | Hyuk Lee | David Khirkuli | Hyuk Lee | Piotr Alexewicz | **Vincent Ong** |

There seems to be fairly broad agreement on the top two contestants in the second round, and arguably the third place winner.

Vincent Ong did not appear in the top five in any of the voting methods considered. Vincent came in 6th place in first past the post, 7th place in Copeland ranking, and 6th place in instant runoff voting.  However, he came in 32nd place in the bottom-elimination method.  This means that while there were many judges who gave Vincent Ong a high ranking, there were some who gave him a low ranking.

In terms of determining the 20 contestants to pass on to Stage 3, there were 14 discrepancies with the first past the post method, 2 discrepancies with the instant runoff voting, and 4 discrepancies with the bottom elimination voting.

For passing on to the Stage 3, Copeland’s method agreed 100% with the Competition method, providing more evidence that Copeland’s method is most similar to the Competition method in its effects.

## Stage 3

In Stage 3, of the 20 contestants competing, the following five contestants got the highest scores on each of the voting systems:

_Table 3:  Stage 3 voting results_

| Rank | FIrst past the post | COPELAND’s Method | INSTANT RUNOFF VOTING | BOTTOM ELIMINATION VOTING | COMPETITION METHOD |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Eric Lu | Eric Lu | Eric Lu | Eric Lu | **Eric Lu** |
| 2 | Zitong Wang | Zitong Wang | Zitong Wang | Zitong Wang | **Kevin Chen** |
| 3 | Kevin Chen | Tianyou Li | Kevin Chen | Kevin Chen | **Zitong Wang** |
| 4 | Tianyou Li | Kevin Chen | Tianyou Li | Tianyou Li | ****Tianyou Li**** |
| 5 | Yang (Jack) Gao | Tianyai Lyu | Yang (Jack) Gao | Shiori Kuwahara | **Shiori Kuwahara** |

Every method agrees that Eric Lu was first place in this round, and all of the methods, except for the method actually used, predict that Zitong Wang came in second.

Interestingly, this time, the five top people chosen by the Jury were the same as the five top people chosen by the bottom-elimination method. It as if we have gone from asking who would win the most in pairwise competitions to asking who does nobody rank lowly.

In terms of the 11 contestants passing on to the Final Stage, there were 3 discrepancies with the first past the post method, 2 discrepancies with the instant runoff voting, and 2 discrepancies with the bottom elimination voting.

Once again, Copeland’s method agreed 100% with the Competition method on who should pass on to the Final Stage, providing yet more evidence that Copeland’s method is most similar to the Competition method in its effects.

## Final stage

In the Final stage, of the 11 contestants competing, the following five contestants got the highest scores under each of the voting systems:

_Table 4:  Final Stage voting results_

| Rank | FIrst past the post | COPELAND’s Method | INSTANT RUNOFF VOTING | BOTTOM ELIMINATION VOTING | COMPETITION METHOD |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Tianyao Lyu | Eric Lu | Kevin Chen | Eric Lu | **Eric Lu** |
| 2 | Vincent Ong | Kevin Chen | Vincent Ong | Kevin Chen | **Kevin Chen** |
| 3 | Kevin Chen | Piotr Alexewicz | Tianyao Lyu | Piotr Alexewicz | **Zitong Wang** |
| 4 | Eric Lu | Tianuao Lyu | Eric Lu | Shiori Kuwahara | **Tianyao Lyu** |
| 5 | Piotr Alexewicz | Vincent Ong | Shiori Kuwhara | Zitong Wang | **Shiori Kuwahara** |

Two of the four voting methods considered here agree with the Competition method that Eric Lu was the winner, and Eric Lu appears in the top 4 under all voting systems considered.

Kevin Chen came in first on instant runoff voting, third on first past the post voting, and second with the other two methods, so the judgement of the Jury that Kevin Chen was second also seems fairly robust. (Although, the average position of Kevin Chen across the four voting systems was closer to first place than the average position of Eric Lu across the four systems.)

Zitong Wang was 7th in first past the post, 9th in Copeland ranking, and 8th in instant runoff voting. Zitong Wang seems to have made third place by not being near the bottom of anybody’s list, but he was favored by few.

## Final stage, cumulative voting

I did an additional analysis where instead of considering the judges’ vote only in the Final Stage, I treated it as if there were 68 judges (4 x 17), considering all of the votes the contestants received from all of the judges in all of the rounds. I treated them as if Stage 1 Garrick Ohlsson was a different judge than Stage 2 Garrick Ohlsson. The link to the spreadsheet containing the full results of this analysis can be found [here](https://github.com/KCaldeira/chopin_voting/tree/main/data/output).

One could argue that it is good to take into consideration the scores from all the Stages in the final scoring, to reduce the influence of any one performance.

Under this cumulative voting approach, the following five contestants got the highest scores on each of the voting systems:

_Table 5:  Voting results taking into consideration votes by the judges across all stages._

| Rank | FIrst past the post | COPELAND’s Method | INSTANT RUNOFF VOTING | BOTTOM ELIMINATION VOTING | COMPETITION METHOD |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Kevin Chen | Eric Lu | Kevin Chen | Eric Lu | **Eric Lu** |
| 2 | Eric Lu | Kevin Chen | Eric Lu | Kevin Chen | **Kevin Chen** |
| 3 | Vincent Ong | Shiori Kuwahara | Vincent Ong | Shiori Kuwahara | **Zitong Wang** |
| 4 | Zitong Wang | Vincent Ong | Shiori Kuwahara | Tianyao Lyu | ****Tianyao Lyu**** |
| 5 | Tianyao Lyu | Zitong Wang | Zitong Wang | Miyu Shindo | **Shiori Kuwahara** |

## CONCLUDING COMMENTS

Copeland’s method and instant runoff voting are both typically considered relatively good voting systems, and these two voting systems would have produced different first place winners for this year’s competiton.

There is no objective way to say what would be the “best” voting system. The right voting system to use for this year’s competition was the voting system defined in the rules of the competition.

I would suggest that in future years, the Competition consider using Copeland’s method. Copeland’s method produced the results that were closest to the results obtained under the current methodology, but is a simple and widely recognized approach that has been studied in detail by mathematicians and game theorists.

Copeland’s method is not guaranteed to produce a single winner, known as [a Condorcet winner](https://en.wikipedia.org/wiki/Condorcet_winner_criterion). Therefore, a tiebreak procedure might be considered.  A reasonable tiebreak might be to choose which of the people tied for first place under Copeland’s method does best on instant runoff voting.

Purely numerical approaches give more weight to judges who use a wide range of values in their voting, whereas methods based on ranking are less amenable to one judge having more influence than another judge.

First past the post voting is generally considered to be a bad voting system, although it is used in the UK and many other places.  Bottom elimination is better at weeding out the worst than at finding the best.

Lastly, I would encourage the competition to consider developing more awards, maybe not open to the first prize winner. Who played most emotively? Who displayed the greatest technical skill? Who was the most polarizing?

I’ve been listening to Eric Lu since the Competition’s results were announced, but now I want to go back and listen to some others, realizing the “best” is a matter of taste, and even one person’s taste can differ from day to day or even hour to hour.

In particular I want to look at which contestants produced the widest divergence of opinions among the judges. Which set of judges would I agree with?  And who will I like the most?

The only way to find out is to listen.

## ADDENDUM

## Normalized mean analysis

The above looks at ranking voting systems, but one can approach this problem numerically.

Numerical voting systems have the problem that different judges have different amount of influence on rankings depending on both their average score and how large a range they use for their scoring.

One way to adjust for this is to subtract the mean score given by each judge and divide by the standard deviation of their scores. This gives each judge the same average and the same amount of variability.

We can then rank people at each stage by this normalized mean score of the judges. A spreadsheet that does this analysis can be found [here](https://github.com/KCaldeira/chopin_voting/tree/main/data/output).

For the Final Stage, the results for the top 5 contestants in terms of normalized mean scores are:

_Table A1: Normalized mean analysis_

| Rank | Contestant | Normalized Mean ± 1 STD ERROR | Normalized Standard deviation |
| :---: | --- | :---: | :---: |
| 1 | Kevin Chen | 0.50 ± 0.20 | 0.83 |
| 2 | Eric Lu | 0.48 ± 0.19 | 0.72 |
| 3 | Piotr Alexewicz | 0.36 ± 0.19 | 0.79 |
| 4 | Vincent Ong | 0.18 ± 0.29 | 1.18 |
| 5 | Shiori Kuwahara | 0.13 ± 0.22 | 0.90 |

There is a mathematical way to estimate the uncertainty on these scores, how much the scores would be expected to vary if you hypothetically chose a different 17 judges from the same pool of possible judges (if such a thing exists). This amount is known as “standard error”.

In my scientific work, usually results need to differ by two standard errors before we consider them statistically significant. By this measure, none of the top competitors would be considered to differ to a statistically significant degree.

I would go further and say that the Kevin Chen and Eric Lu’s scores are statistically indistinguishable.

## Least agreement analysis

Above, I said it would be interesting to know which pianists created the greatest difference of opinion among the judges.

Based on normalized standard deviations as described above, in Stage 1, the contestants with the most disagreement among judges was a mix of high , mid and low ranked contestants:   Xiaoyu Hu, Piotr Pawlak, Vincent Ong, Xuanyi Mao, and Gabriele Strata. In contrast, the contestants where was the most agreement were all ranked low.

In Stage 2, the contestants where there was the most disagreement were William Yang, Yang (Jack) Gao, David Khrikuli, Gabriele Strata, and Vincent Ong, who were all high to middle ranked. Most of the contestants where there was high agreement were low ranked with the exception of Eric Lu, where there was high agreement that he was very good.

In Stage 3, the most disagreement were middle to low ranked contestants: Yang (Jack) Gao, Piotr Pawlak, David Khrikuli, William Yang, and Vincent Ong. The contestants where there was the most agreement were also middle to low ranked contestant, once again with the exception of Eric Lu, where there was high agreement that he was very good.

For the Final Stage, of the people in the top five shown in Table A1, there was the most disagreement about Vincent Ong, with the highest normalized standard deviation of any contestant in the Final Stage.

It looks to me like VIncent Ong wins the prize for being considered among the top finalists despite having the most disagreement among the judges.  He is who I want to listen to now. (And then Kevin Chen.)
