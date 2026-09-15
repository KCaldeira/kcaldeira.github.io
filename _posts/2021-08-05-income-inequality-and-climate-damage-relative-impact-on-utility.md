---
layout: post
title: "Income inequality and climate damage: Relative impact on utility"
date: 2021-08-05T10:33:42+00:00
slug: income-inequality-and-climate-damage-relative-impact-on-utility
wp_id: 1853
---

WHAT WOULD THE DICE MODEL DAMAGE AND UTILITITY FUNCTIONS SAY ABOUT RELATIVE VALUE IN ADDRESSING INCOME INEQUALITY VS. CLIMATE CHALLENGES?

{% include figure.html src="/assets/images/2021/08/20210710_192002.jpg" caption="Dog deriving utility by watching a dog on television." %}

[Nordhaus’s DICE model](https://williamnordhaus.com/dicerice-models) represents utility as population times per capita utility, and it represents per capita utility as increasing with per-capita consumption to the 0.45 power.

{% include figure.html src="/assets/images/2021/08/clipboard01-1-2.jpg" caption="[http://www.econ.yale.edu/~nordhaus/homepage/homepage/DICE2013R_100413_vanilla.gms](http://www.econ.yale.edu/~nordhaus/homepage/homepage/DICE2013R_100413_vanilla.gms)" %}

A lot of attention has been paid to the issue of temporal discounting in quantifying current value of future costs and benefits. That is, a lot of attention has been paid to assessing how we should value future generations relative to our own, but relatively less attention has been paid to addressing how we should value others living today relative to ourselves.

To address this issue, I thought I would look at the increase in total utility that would be predicted by the DICE utility functions under an assumption of income equality and compare that with the change in utility expected to come from addressing the climate change problem.

That is, what would the predicted change in utility be if everyone were brought to the mean income.  (Before people start complaining, I too have read Kahneman and Ariely and understand that real utility is far more complicated than represented in the DICE model.)

{% include figure.html src="/assets/images/2021/08/global-inc-distribution-2003-and-2013-1-750x525-1-2.png" caption="[https://ourworldindata.org/global-economic-inequality](https://ourworldindata.org/global-economic-inequality)" %}

Another view of this data is:

{% include figure.html src="/assets/images/2021/08/2-world-income-distribution-2003-to-2035-1.png" caption="[https://ourworldindata.org/global-economic-inequality](https://ourworldindata.org/global-economic-inequality)" %}

Unfortunately, I did not find a location to download this data easily. (I’ll fix up this blog post when I find it.) Therefore, I will just do a very rough-and ready analysis.  Since they give us the median and the mean, let’s just assume this is a log-normal distribution with that median and mean.

Luckily, trusty Wikipedia gives us the appropriate formulas for the median and mean of a lognormal distribution:

{% include figure.html src="/assets/images/2021/08/clipboard02.jpg" %}

{% include figure.html src="/assets/images/2021/08/clipboard03.jpg" caption="[https://en.wikipedia.org/wiki/Log-normal_distribution](https://en.wikipedia.org/wiki/Log-normal_distribution)" %}

For a mean income of $5375/year and a median income of $2010/year, this yields mu = 7.6 and sigma = 1.4.  (We will forgo pretense to greater accuracy.)  Density of people making X $/yr can be estimated by plugging in these numbers into the lognormal function above.

If we now assume that utility goes with income to the 0.45 power, we can calculate that  global utility is 78% of what it would be were income distributed evenly. That is, this analysis suggests we are taking a 22% hit on global utility due to income inequality.

This 22% reduction in global utility is of the same order of magnitude as some of the more high-end climate damage estimates and an order of magnitude larger than many climate damage estimates.

This suggests that if we are interested in human welfare, addressing income inequality may be as important as addressing climate challenges.

I know this is just a back-of-envelope calculation and human psychology is a lot more complicated than income raised to the 0.45 power and climate damage is a lot more complicated than temperature squared. No doubt there are complicated relationships between income distributions, capital accumulation, and economic growth. Nevertheless, this analysis suggests that income inequality may be regarded as a challenge to human welfare that is on a scale comparable to that of the climate problem.

Lastly, I would just like to point out that there are two ways of decreasing income inequality: increasing incomes at the lower end of the spectrum and decreasing incomes at the upper end of the spectrum. While some of both strategies may prove useful, it is only by increasing incomes at the lower end of the spectrum that we can increase aggregate utility without decreasing anyone’s individual utility.  Thus, while income redistribution may have important roles to play, this suggests that economic development will be the leading player in increasing global aggregate utility.

{% include figure.html src="/assets/images/2021/02/image-1-2.png" %}
