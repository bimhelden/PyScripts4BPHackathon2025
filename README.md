# "UserDefined" meets native IFC

This repository hosts and publishes the results of our Hackathon project, where we explored how to fulfill data requirements that seem to go beyond the official IFC standard.

## Challenge

How can we ensure that data owners and stakeholders get the information they require, while staying compliant with IFC?  

Our **hypothesis**:  
Most of the requested data is not actually missing. It is already created by BIM authors and their tools.  
If not, it raises the question: are we using the right tools in the first place?

The **main challenge** is therefore not producing new data, but matching the available data from engineers with the expectations of the owner, namely property names and object types.

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

Feel free to use, adapt, and contribute.

