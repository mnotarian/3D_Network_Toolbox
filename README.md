# 3D Network Toolbox - Expanded Version

Using an input pedestrian network and a Digital Elevation/Terrain Model (DEM/DTM), this Python Toolbox for ArcGIS Pro/10.4 or greater implements Tobler’s Hiking Function and/or other walking velocity equations to enable the calculation of slope-aware travel times for walking travel on a 3D network. Additionally, it also calculates energy expended carrying loads of varying weights along the same network. Follow [these steps](https://pro.arcgis.com/en/pro-app/help/analysis/geoprocessing/basics/use-a-custom-geoprocessing-tool.htm) to add the ```.pyt``` toolbox to your project.

<img width="500" alt="3d_network" src="https://github.com/higgicd/3D_Network_Toolbox/blob/master/assets/img/3D_NetworkToolbox.jpg">

## Updates
- May 2022
  - Fork added with expanded version that includes additional velocity equations (Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso [2017], Irsmischer and Clarke [2018], modified Toblers) and metabolic energy output from Pandolf, Givoni and Goldman (1977) with Santee et al. (2003) correction factor for negative gradients
   
- July 2020
  - pushed an update to the toolbox to fix issues that were preventing it from working correctly
  - added some help xml

- January 2018
  - Tool requires the 3D Analyst and Spatial Analyst extensions  
  - Network analysis requires the Network Analyst extension  
  - The tool presently only works with **metric** units and is coded to expect values in **meters**

## Overview
With an input 2D network and a DEM/DTM, this tool performs several steps:

1) Interpolate the 3D shape of the network given the DTM
2) Split the original network edges into smaller segments
3) Calculate the average slope of these segments
4) Calculate the estimated pedestrian velocity given the slope of the terrain
5) Calculate the estimated walking times and energy costs for each segment of the network

Options are given to control the granularity of results and specify any edges you do not want to be split or not have slope-aware travel times. See the detailed explanation below. Original tool applied in [Higgins (2019)](https://doi.org/10.1016/j.landurbplan.2018.12.011). Expanded tool applied in Notarian (forthcoming 2023). If you use this for research purposes, please cite these papers.

## Detailed Workflow
Given a 2D network and a Digital Elevation/Terrain Model (DTM), this toolbox interpolates the 3D shape of the network on the DTM. The tool then splits the network into smaller segments and determines the average slope of these segments based on their start and end point XYZ-coordinates. 3D lengths for each line are also interpolated. Next, the tool estimates the travel time in minutes to traverse the segment given the average slope using various walking equations. These are briefly described below.

**Tobler’s (1993) Hiking Function**:

>  *v* = 6exp(-3.5|*m* + 0.05|)

where *v* is kph, and  *m* is the gradient of the terrain, defined as either *tan*(*θ*) with *θ* as the slope of the terrain in degrees or *dh*/*dx* with *dh* and *dx* as the change in height and distance respectively. This results in the following travel time function:

<img width="500" alt="toblerfunction" src="https://github.com/higgicd/3D_Network_Toolbox/blob/master/assets/img/ToblerFunction.jpg">

The offset in Tobler’s function specifies a maximum walking velocity of 1.67 meters per second (6kph) when walking on a slight downhill gradient of -5%. On flat ground, pedestrian velocity is 1.4 meters per second, or 5kph. Because of the directionality in Tobler's function, walk times are calculated for the From-To (FT) and To-From (TF) directions for network edges.

**Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017)**:<br>
A modified version of Tobler's function that better approximates empirical crowdsourced hiking data.

> *v* = 4.8exp(-5.3|(*m* × 0.7)+0.03|

**Irmischer and Clarke (2018)**:<br>
Equation fitted to hiker data collected via GPS.

> *v* = *f* (0.11 + exp(-(*s* + 5)<sup>2</sup>/(2 × 30<sup>2</sup>)) 3.6

where *v* is m/s, *f*=1 for a male hiker on-path and *f*=0.95 for a female hiker on-path, and *s* is percent slope.

**Tobler 3.5 kph Maximum**:<br>
A modified version of Tobler's function (see Notarian 2023) that specifies a maximum walking velocity of 3.5 kph at a gradient of -5% (in place of the original equation's 5 kph). Note: experimental, not based on empirical data.

>  *v* = 3.5exp(-3.5|*m* + 0.05|)

**Tobler Urban Adjustment**:<br>
A modified version of Tobler's function with a correction factor of 0.6 to approximate slower movement within a crowded urban environment. Note: experimental, not based on empirical data.

>  *v* = 6exp(-3.5|*m* + 0.05|)0.8

<img width="700" alt="equations" src="https://github.com/mnotarian/3D_Network_Toolbox/blob/8e91b500459a71e48a09bc39ac69f09228b9b35c/assets/img/Equations.jpg">

**Pandolf Load Carriage Equation**:<br>
Metabolic energy costs are calculated using the Pandolf load carriage equation (Pandolf, Givoni and Goldman 1977).

> *M* = 1.5*W* + 2(*W* + *L*) (*L* / *W*)<sup>2</sup> + *η*(*W* + *L*)(1.5*V* <sup>2</sup> + 0.35*VS*)

Output (*M*) is in watts, where *W* is the individual body mass (kg), *L* is the carried load (kg), *V* is walking speed (m/s), *S* is slope (percent), and *η* a terrain factor. The output is transformed into calories (kcals) by converting to kcals/min (watts × 0.014330754 = kcals/min) and then multiplying these values by the segment time cost as derived using the walking equations.

For all negative gradients, a correction factor proposed by Santee et al. (2003) is subtracted from the Pandolf equation:

> *CF* = -*η*[ ((*G*(*M*+*L*)*V*) / 3.5) – ((*W*+*L*) (*G*+6)<sup>2</sup> / *W*) + (25*V* <sup>2</sup>) ]

where *η* is a terrain factor. In the current version, *η* is set to 1 represent movement on paved surfaces.

### Tool Inputs

<img width="650" alt="toolcapture" src="https://github.com/mnotarian/3D_Network_Toolbox/blob/6569d1817b860344cae801a00a91601cbd08616a/assets/img/ToolCapture_scaled.JPG">

- **Input Surface**: Digital elevation/terrain model.
- **Input Network (2D)**: The input planar pedestrian network. Can be obtained from any number of sources. The OSMnx tool (Boeing, 2017) makes the collection and preparation of OpenStreetMap networks particularly easy.
- **Sample Distance**: The distance at which to split the edges of the network to calculate their slope and travel time. The selection of this variable determines the slope detail in the network and should be based on some tradeoff between your desired network slope resolution and the resolution of the DTM, as this can dramatically increase the number of edges in your network. In [Higgins (2019)](https://doi.org/10.1016/j.landurbplan.2018.12.011) for example, a sample distance of 10m was determined to be a reasonable compromise with a DTM available at a 2m resolution. Short of Network Analyst continuously differentiating over network segments to find their slope (which it cannot do), splitting up longer lines into smaller segments to calculate their average slope is an effective compromise for implementing slope-based travel times into the networks.
- Network has **No Split** edges (*optional*): If checked, this parameter indicates that your input 2D network has lines that should not be split by the tool. Useful for line features like bridges, where the standard interpolation and line splitting work flow could result in these edges traversing up and down the steep sides of a ravine in the DTM.
  - ```NO_SPLIT```: A field in the pedestrian network that takes a value of 1 for any edges that will not be split by the tool. If you would like to use the No Split option, the tool is presently **hard coded** to expect a field ```NO_SPLIT``` in the input 2D network. With ```NO_SPLIT = 1```, these edges will have the height of their start and end point coordinates interpolated from the DTM, but will not be split further. Slope, and slope-aware travel times will still be calculated based on the average slope of the unsplit line’s start and end points in 3D space. If you tick the *No Split* box but do not have any ```NO_SPLIT``` links identified, the tool will not work properly. We will try to make this more user-friendly in a future release.
- Network as **No Slope** edges (*optional*): If checked, this parameter indicates that your input 2D network has edges that should not have their travel time based on the slope of the terrain. Useful for any network elements that you do not want to have 3D, slope-aware travel times, such as internal pathways in buildings or pedestrian subways. If slope were applied, would result in inaccurate estimates of travel time.
  - ```NO_SLOPE```: A field in the pedestrian network that takes a value of 1 for any edges for which their travel time will be based on an assumed flat plane.  If you would like to use the No Split option, the tool is presently **hard coded** to expect a field ```NO_SLOPE``` in the input 2D network. With ```NO_SLOPE = 1```, these edges still have their height interpolated from the DTM, but these values are not used to calculate their travel time; the 2D travel time is used instead. This is done to maintain network topology when creating a network that uses the geometry of features for elevation in Network Analyst.
- **Individual Body Mass (kg)**: The body weight of the individual, used to calculate metabolic energy costs. The default value of 80 can be changed.
- **Enter Multiple Load Weights (kg)**: Several load weights can be entered, used to calculate metabolic energy costs.
- **Velocity Equation**: Choose at least one equation to calculate walking speed. Mutiple equations can be chosen. 

### Tool Outputs
- **Output Network (3D)**: The output 3D pedestrian network for further analysis. The network has the following new fields. Some fields are created only if the relevant velocity equations are checked in the dialog box:
  - **Calcuation Fields**: These fields are used to solve the various equations.
    - ```Start_Z```: Start point Z-coordinate of the line interpolated from the DTM, based on its original digitization direction.
    - ```End_Z```: End point Z-coordinate of the line interpolated from the DTM, based on its original digitization direction.
    - ```Max_Z```: Maximum height value of the line interpolated from the DTM.
    - ```Length3D```: 3D length of the line.
    - ```Avg_Slope```: Absolute percent slope of the line.
    - ```SlopePctTF```: Percent slope of the line segment in the To-From direction.
    - ```SlopePctFT```: Percent slope of the line segment in the From-To direction.
  - **Velocity Fields**: These fields contain the speed to traverse the line segment.
    - ```TF_MpSTob```: Speed (m/s) along the line segment slope in the To-From direction, based on the original Tobler's Hiking Function.
    - ```FT_MpSTob```: Speed (m/s) along the line segment slope in the From-To direction, based on the original Tobler's Hiking Function.
    - ```TF_MpS_MP```: Speed (m/s) along the line segment slope in the To-From direction, based on Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017).
    - ```FT_MpS_MP```: Speed (m/s) along the line segment slope in the From-To direction, based on Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017).
    - ```TF_MpS_ICF```: Speed (m/s) along the line segment slope in the To-From direction, based on Irmischer and Clarke (2018) on-path female hiker.
    - ```FT_MpS_ICF```: Speed (m/s) along the line segment slope in the From-To direction, based on Irmischer and Clarke (2018) on-path female hiker.
    - ```TF_MpS_ICM```: Speed (m/s) along the line segment slope in the To-From direction, based on Irmischer and Clarke (2018) on-path male hiker.
    - ```FT_MpS_ICM```: Speed (m/s) along the line segment slope in the From-To direction, based on Irmischer and Clarke (2018) on-path male hiker.
    - ```TF_MpS35k```: Speed (m/s) along the line segment slope in the To-From direction, based on Tobler's Hiking Function modified with a maximum velocity of 3.5 kph.
    - ```FT_MpS35k```: Speed (m/s) along the line segment slope in the From-To direction, based on Tobler's Hiking Function modified with a maximum velocity of 3.5 kph.
    - ```TF_MpSUrb```: Speed (m/s) along the line segment slope in the To-From direction, based on the modified "Urban Adjustment" Tobler's Hiking Function.
    - ```FT_MpSUrb```: Speed (m/s) along the line segment slope in the From-To direction, based on the modified "Urban Adjustment" Tobler's Hiking Function.
  - **Time Fields**: These fields contain the time to traverse the line segment.
    - ```FT_MIN_2D```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 2D length of the line and the flat-ground walking speed of about 5kph.
    - ```TF_MIN_2D```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 2D length of the line and the flat-ground walking speed of about 5kph.
    - ```FT_MIN_3D```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from the original Tobler's Hiking Function ((```End_Z```-```Start_Z```)/2D length of the line).
    - ```TF_MIN_3D```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from the original Tobler's Hiking Function ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```FT_MIN_MP```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017) ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```TF_MIN_MP```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017) ((```End_Z```-```Start_Z```)/2D length of the line).
    - ```FT_MIN_ICF```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Irmischer and Clarke (2018) on-path female hiker ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```TF_MIN_ICF```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Irmischer and Clarke (2018) on-path female hiker ((```End_Z```-```Start_Z```)/2D length of the line).
    - ```FT_MIN_ICM```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Irmischer and Clarke (2018) on-path male hiker ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```TF_MIN_ICM```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Irmischer and Clarke (2018) on-path male hiker ((```End_Z```-```Start_Z```)/2D length of the line).
    - ```FT_MIN_35k```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Tobler's Hiking Function modified with a maximum velocity of 3.5 kph ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```TF_MIN_35k```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from Tobler's Hiking Function modified with a maximum velocity of 3.5 kph ((```End_Z```-```Start_Z```)/2D length of the line).
    - ```FT_MIN_Urb```: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from the modified "Urban Adjustment" Tobler's Hiking Function ((```Start_Z```-```End_Z```)/2D length of the line).
    - ```TF_MIN_Urb```: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment derived from the modified "Urban Adjustment" Tobler's Hiking Function ((```End_Z```-```Start_Z```)/2D length of the line).
  - **Metabolic Energy Fields**: These fields contain the energy costs to traverse the line segment, output in kcals for every chosen walking velocity equation and load weight entered. **NOTE**: In each field, #LoadMass# and #BodyMass# will be represented by the entered values. For example, ```FTSt_#LoadMass#_#BodyMass#``` becomes ```FTSt_12_65``` for a 65 kg individual carrying a 12 kg load.

    - ```FTSt_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using the original Tobler's Hiking Function.
    - ```TFSt_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using the original Tobler's Hiking Function. 
    - ```FTMP_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017).
    - ```TFMP_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using Márquez-Pérez, Vallejo-Villalta, and Álvarez-Francoso (2017).
    - ```FTIF_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using Irmischer and Clarke (2018) on-path female hiker.
    - ```TFIF_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using Irmischer and Clarke (2018) on-path male hiker.
    - ```FTIM_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using Irmischer and Clarke (2018) on-path female hiker.
    - ```TFIM_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using Irmischer and Clarke (2018) on-path male hiker.
    - ```FT35_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using Tobler's Hiking Function modified with a maximum velocity of 3.5 kph.
    - ```TF35_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using Tobler's Hiking Function modified with a maximum velocity of 3.5 kph.
    - ```FTUr_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the From-To direction using the modified "Urban Adjustment" Tobler's Hiking Function.
    - ```TFUr_#LoadMass#_#BodyMass#```: Kcals to traverse the line segment in the To-From direction using the modified "Urban Adjustment" Tobler's Hiking Function.

### Creating your Network Dataset
With the tool complete, you can now make a 3D pedestrian network using Network Analyst in ArcGIS. In particular, users can model elevation using feature geometry and specify the ```TravelTime_3D``` (using the ```FT_MIN_3D``` and ```TF_MIN_3D``` fields or any other time output fields) cost attribute in **minutes**. A second ```TravelTime_2D``` (using the ```FT_MIN_2D``` and ```TF_MIN_2D``` fields) cost attribute can be specified and compared with results from the ```TravelTime_3D``` cost attribute to reveal the estimated impact on pedestrian travel when taking slope into account. Users can also specify any of the metabolic energy output fields as the cost attribute in **calories**.

## References

Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126-139. DOI: [10.1016/j.compenvurbsys.2017.05.004](https://doi.org/10.1016/j.compenvurbsys.2017.05.004)

Higgins, C. (2019). A 4D spatio-temporal approach to modelling land value uplift from rapid transit in high density and topographically-rich cities. *Landscape and Urban Planning*. *185*, 68-82. DOI: [10.1016/j.landurbplan.2018.12.011](https://doi.org/10.1016/j.landurbplan.2018.12.011)

Irmischer, I., and K. Clarke. (2018). Measuring and modeling the speed of human navigation. *Cartography and Geographic Information Science* 45, 177–186. DOI: [10.1080/15230406.2017.1292150](https://doi.org/10.1080/15230406.2017.1292150)

Márquez-Pérez, J., I. Vallejo-Villalta, and J.I. Álvarez-Francoso. (2017). Estimated travel time for walking trails in natural areas. *Geografisk Tidsskrift-Danish Journal of Geography* 117, 53–62. DOI: [10.1080/00167223.2017.1316212](https://doi.org/10.1080/00167223.2017.1316212)

Notarian, M. (2023). A Spatial Network Analysis of Water Distribution from Public Fountains in Pompeii. *American Journal of Archaeology*, 127.1 (forthcoming)

Pandolf, K.B., B. Givoni, and R.F. Goldman. (1977). “Predicting energy expenditure with loads while standing or walking very slowly.” *Journal of Applied Physiology* 43,  577–81.

Santee, W.R., L.A. Blanchard, K.L. Speckman, J.A. Gonzalez, and R.F. Wallace. (2003). Load Carriage Model Development and Testing with Field Data. Technical Note No. ADA#415788. Natick, MA: Army Research Institute of Environmental Medicine.

Tobler, W. (1993). Three presentations on geographical analysis and modeling: Non-isotropic geographic modeling speculations on the geometry of geography global spatial analysis. *National center for geographic information and analysis*. 93(1).
