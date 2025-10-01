# "UserDefined" meets native IFC

This repository hosts and publishes the results of our Hackathon prototype, where we explored how to fulfill data requirements that seem to go beyond the official IFC standard.

The project was developed by **Team Bonsai** during the [Hackathon 2025 organized by BIM Deutschland](https://www.bimdeutschland.de/veranstaltungen/hackathon-2025).  
The Hackathon brought together 13 teams and gave us a great chance to share ideas with other developers. You can read more in the [press release of the Federal Ministry for Digital and Transport (BMV)](https://www.bmv.de/SharedDocs/DE/Pressemitteilungen/2025/044-bim-hackathon.html).  

We are proud that our work was recognized with the [**3rd prize**](https://www.bimdeutschland.de/das-sind-die-gewinner-vom-hackathon-2025-zum-bim-portal-des-bundes).  


## Challenge

How can we make sure that owners and stakeholders get the data they need, while staying consistent with established design processes supported by BIM authoring tools, ideally relying on native IFC?

Our **hypothesis**:  
Most of the requested data isn’t really missing — it’s already created by BIM authors and their tools.
If that’s not the case, it raises an important question: are we using the right tools, and are we following the right processes in the first place?

The **main challenge** is therefore not to generate new data, but to align the data provided by engineers with the owner's expectations - in simple terms, to use the correct property names and object types.

![Slide: Challenge](https://github.com/bimhelden/PyScripts4BPHackathon2025/blob/master/Images/challenge.png) 

## Approach

In our "Bonsai" team with [Volker Krieger](https://www.linkedin.com/in/volker-krieger-b3328115/), [Bernd Gmeiner](https://www.linkedin.com/in/bernd-gmeiner-16134a21/) and [Matthias Weise](https://www.linkedin.com/in/matthias-weise-17363970/) we developed a three-step approach, implemented as extensions into the **BonsaiBIM** framework:

1. **IDS Fetch** – import the data requirements in a machine-readable specification  
2. **IDS Match** – compare requested vs. available data using IDS as the backbone  
3. **IFC Patch** – apply automated adjustments to the BIM based on the matching definition  

![Slide: Idea](https://github.com/bimhelden/PyScripts4BPHackathon2025/blob/master/Images/idea.png) 

## Results

- Prototypes developed and tested during the Hackathon (extensions for Blender with BonsaiBIM) - in this Github repository 
- [Documentation with additional background information](https://tinyurl.com/HackWithBonsai)  
- [Slides of our pitch presentation given at the Hackathon](https://docs.google.com/presentation/d/1naV-daRNee5Q6QzOEVW35zfekk-QYCfomJKkVbIFafY/edit?usp=sharing)  

## Next Steps

- Within the Hackathon team, we are discussing how to further develop this initial idea.  
- Together with my colleagues at [**AEC3**](https://www.aec3.de/), we are exploring how to actively support this use case.  

Feel free to reach out to us if you are interested in this work or would like to use, adapt and contribute.

