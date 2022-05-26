# 3D Network Toolbox for ArcGIS 10.x
    # Christopher D. Higgins
    # Jimmy Chan
    # Department of Land Surveying and Geo-Informatics
    # The Hong Kong Polytechnic University
    # Expanded by Matthew Notarian
    # Hiram College
    
import arcpy, os
  
class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "3D Network Toolbox"
        self.alias = "Network3D"

        # List of tool classes associated with this toolbox
        self.tools = [Network2DTo3D]

class Network2DTo3D(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3D Network Generation from 2D Network and DEM"
        self.description = "Generate 3D Network from 2D Network using Digital Terrain Model. This version is compatible on ArcGIS 10.4 or later."

        self.canRunInBackground = True
        self.category = "3D Network Generation"
        
    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Surface",
            name="Input_Surface",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Input Network (2D)",
            name="Input_Line_Feature_Class",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Sample Distance",
            name="Distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param2.filter.type = "Range"
        param2.filter.list = [1.0,  float("inf")]
        param2.defaultEnvironmentName = 10.0
        param2.value = 10.0

        param3 = arcpy.Parameter(
            displayName="Network has No Split edges",
            name="FalseSplit",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param3.value = False
        
        param4 = arcpy.Parameter(
            displayName="Network has No Slope edges",
            name="FalseSlope",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param4.value = False

        param5 = arcpy.Parameter(
            displayName="Output Network (3D)",
            name="Network_3D",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        param6 = arcpy.Parameter(
            displayName="Individual Body Mass (kg)",
            name="BodyMass",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param6.filter.type = "Range"
        param6.filter.list = [1.0,  float("inf")]
        param6.defaultEnvironmentName = 80.0
        param6.value = 80.0
        
        param7 = arcpy.Parameter(
            displayName="Enter Multiple Load Weights (kg)",
            name="Vessel",
            datatype="GPValueTable",
            parameterType="Required",
            direction="Input",
            multiValue=True)
            
        param7.columns =([["GPDouble", "Load Weight in kg"]])
        
        param8 = arcpy.Parameter(
            displayName='Velocity Equation',
            name='velocity_eq',
            datatype='String',
            parameterType='Required',
            direction='Input',
            multiValue=True)

        param8.filter.type = "ValueList"
        param8.filter.list = ['Standard Tobler', 'Marquez-Perez et al.', 'Irmischer and Clarke Male On-Path', 'Irmischer and Clarke Female On-Path', 'Tobler 3.5 kmh max', 'Tobler Urban Adjustment']
        
        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("3D") != "Available" or arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
                return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return   

    def execute(self, parameters, messages):

        arcpy.CheckOutExtension("3D")
        arcpy.CheckOutExtension("Spatial")
        
        input_surface = parameters[0].valueAsText
        input_lines = parameters[1].valueAsText
        sample_dist = parameters[2].value
        flag_nosplit = parameters[3].valueAsText
        flag_noslope = parameters[4].valueAsText
        output_lines = parameters[5].valueAsText
        body_mass = parameters[6].value
        loadlist = parameters[7].value
        import itertools
        veslist = list(itertools.chain.from_iterable(loadlist))
        vessel_label = [int(n) for n in veslist]
        arcpy.AddMessage("Using body weight: {0}".format(body_mass))
        arcpy.AddMessage("Using load weights: {0}kg".format(vessel_label))
        search_radius = 0.001
        mass_label = int(parameters[6].value)
        vlist = parameters[8].valueAsText
        arcpy.AddMessage("Using velocity equations: {0}".format(vlist))
        if "Standard Tobler" in vlist:
            st = "st"
        else: 
            st = "no"
        if "Marquez-Perez et al." in vlist:
            mp = "mp"
        else: 
            mp = "no"
        if "Irmischer and Clarke Male On-Path" in vlist:
            icm = "im"
        else:
            icm = "no"
        if "Irmischer and Clarke Female On-Path" in vlist:
            icf = "icf"
        else: 
            icf = "no"
        if "Tobler 3.5 kmh max" in vlist:
            three5 = "35"
        else: 
            three5 = "no"
        if "Tobler Urban Adjustment" in vlist:
            ur = "ur"
        else: 
            ur = "no"
        
        def calculate_z(input_fc):
            MaximumValueFunc = "def MaximumValue(*args): return max(args)"
            
            arcpy.AddField_management(input_fc, "Start_Z", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "End_Z", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "Max_Z", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            
            arcpy.CalculateField_management(input_fc, "Start_Z", "!SHAPE!.firstpoint.Z", "PYTHON_9.3", "")
            arcpy.CalculateField_management(input_fc, "End_Z", "!SHAPE!.lastpoint.Z", "PYTHON_9.3", "")
            arcpy.CalculateField_management(input_fc, "Max_Z", "MaximumValue(!Start_Z!, !End_Z!)", "PYTHON_9.3", MaximumValueFunc)
        
        def tobler_calc(input_fc):
            # Add Z Information
            arcpy.AddZInformation_3d(input_fc, "LENGTH_3D;AVG_SLOPE", "NO_FILTER")
            
            # Add walk time fields
            arcpy.AddField_management(input_fc, "SlopePctTF", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "SlopePctFT", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "FT_MIN_2D", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "TF_MIN_2D", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            if st == "st":
                arcpy.AddField_management(input_fc, "FT_MIN_3D", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MIN_3D", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpSTob", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpSTob", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FTStL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TFStL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass
            if three5 == "35":
                arcpy.AddField_management(input_fc, "TF_MIN_35k", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "") 
                arcpy.AddField_management(input_fc, "FT_MIN_35k", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpS35k", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpS35k", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FT35L{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TF35L{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass
            if ur == "ur":
                arcpy.AddField_management(input_fc, "TF_MIN_Urb", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MIN_Urb", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpSUrb", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpSUrb", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FTURL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TFURL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass
            if mp == "mp":
                arcpy.AddField_management(input_fc, "TF_MIN_MP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MIN_MP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpS_MP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpS_MP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FTMPL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TFMPL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass
            if icf == "icf":
                arcpy.AddField_management(input_fc, "TF_MIN_ICF", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MIN_ICF", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpS_ICF", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpS_ICF", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FTIFL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TFIFL{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass
            if icm == "im":
                arcpy.AddField_management(input_fc, "TF_MIN_ICM", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MIN_ICM", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "TF_MpS_ICM", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(input_fc, "FT_MpS_ICM", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "FTIML{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                for llabel in vessel_label:
                    arcpy.AddField_management(input_fc, "TFIML{0}_{1}".format(llabel, mass_label), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            else:
                pass 
            arcpy.AddField_management(input_fc, "TF_MpS_OP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "FT_MpS_OP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "TF_MIN_OP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(input_fc, "FT_MIN_OP", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            
            # Calculate walk time fields
            arcpy.CalculateField_management(input_fc, "SlopePctTF", "(((!Start_Z!-!End_Z!)/(!shape.length!))*100)", "PYTHON", "") 
            arcpy.CalculateField_management(input_fc, "SlopePctFT", "(((!End_Z!-!Start_Z!)/(!shape.length!))*100)", "PYTHON", "")
            arcpy.CalculateField_management(input_fc, "FT_MIN_2D", "(!shape.length!/(5036.742125))*60", "PYTHON", "")
            arcpy.CalculateField_management(input_fc, "TF_MIN_2D", "(!shape.length!/(5036.742125))*60", "PYTHON", "")
            if st == "st":
                arcpy.CalculateField_management(input_fc, "FT_MIN_3D", "(!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MIN_3D", "(!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpSTob", "(6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))/3.6", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpSTob", "(6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))/3.6", "PYTHON", "")
            else:
                pass
            if three5 == "35":
                arcpy.CalculateField_management(input_fc, "TF_MIN_35k", "(!Length3D!/((3.5*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MIN_35k", "(!Length3D!/((3.5*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpS35k", "(3.5*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))/3.6", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpS35k", "(3.5*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))/3.6", "PYTHON", "")
            else:
                pass
            if ur == "ur":
                arcpy.CalculateField_management(input_fc, "TF_MIN_Urb", "(!Length3D!/(((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*.8)*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MIN_Urb", "(!Length3D!/(((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*.8)*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpSUrb", "((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*0.8)/3.6", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpSUrb", "((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*0.8)/3.6", "PYTHON", "")
            else:
                pass
            arcpy.CalculateField_management(input_fc, "TF_MIN_OP", "(!Length3D!/(((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*.6)*1000))*60", "PYTHON", "")
            arcpy.CalculateField_management(input_fc, "FT_MIN_OP", "(!Length3D!/(((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*.6)*1000))*60", "PYTHON", "")
            if mp == "mp":
                arcpy.CalculateField_management(input_fc, "TF_MIN_MP", "(!Length3D!/((4.8 * (math.exp(-5.3*(math.fabs((( ((!Start_Z! - !End_Z!)/!shape.length!) ) * 0.7)+0.03)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MIN_MP", "(!Length3D!/((4.8 * (math.exp(-5.3*(math.fabs((( ((!End_Z! - !Start_Z!)/!shape.length!) ) * 0.7)+0.03)))))*1000))*60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpS_MP", "(4.8 * (math.exp(-5.3*(math.fabs((( ((!Start_Z! - !End_Z!)/!shape.length!) ) * 0.7)+0.03)))))/3.6", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpS_MP", "(4.8 * (math.exp(-5.3*(math.fabs((( ((!End_Z! - !Start_Z!)/!shape.length!) ) * 0.7)+0.03)))))/3.6", "PYTHON", "")  
            else:
                pass
            if icf == "icf":
                arcpy.CalculateField_management(input_fc, "TF_MIN_ICF", "(!Length3D! / (((0.95 * ((0.11+(math.exp((-((!SlopePctTF! + 5)**2) / 1800.0)))))) * 3.6) * 1000)) * 60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MIN_ICF", "(!Length3D! / (((0.95 * ((0.11+(math.exp((-((!SlopePctFT! + 5)**2) / 1800.0)))))) * 3.6) * 1000)) * 60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpS_ICF", "0.95 * ((0.11+(math.exp((-((!SlopePctTF! + 5)**2) / 1800.0)))))", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpS_ICF", "0.95 * ((0.11+(math.exp((-((!SlopePctFT! + 5)**2) / 1800.0)))))", "PYTHON", "")  
            else:
                pass
            if icm == "im":
                arcpy.CalculateField_management(input_fc, "TF_MIN_ICM", "(!Length3D! / (((0.11+(math.exp((-((!SlopePctTF! + 5)**2) / 1800.0))))*3.6) * 1000)) * 60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MIN_ICM", "(!Length3D! / (((0.11+(math.exp((-((!SlopePctFT! + 5)**2) / 1800.0))))*3.6) * 1000)) * 60", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "TF_MpS_ICM", "(0.11+(math.exp((-((!SlopePctTF! + 5)**2) / 1800.0))))", "PYTHON", "")
                arcpy.CalculateField_management(input_fc, "FT_MpS_ICM", "(0.11+(math.exp((-((!SlopePctFT! + 5)**2) / 1800.0))))", "PYTHON", "")
            else: 
                pass
            arcpy.CalculateField_management(input_fc, "TF_MpS_OP", "((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*0.6)/3.6", "PYTHON", "")
            arcpy.CalculateField_management(input_fc, "FT_MpS_OP", "((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*0.6)/3.6", "PYTHON", "")    
            if st == "st":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpSTob!, !TF_MIN_3D!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TFStL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                    arcpy.AddMessage("Calculating Standard Tobler Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpSTob!, !FT_MIN_3D!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FTStL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

            if mp == "mp":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpS_MP!, !TF_MIN_MP!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TFMPL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                    arcpy.AddMessage("Calculating Marquez-Perez Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpS_MP!, !FT_MIN_MP!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FTMPL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

            if icm == "im":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpS_ICM!, !TF_MIN_ICM!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TFIML{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                    arcpy.AddMessage("Calculating Irmischer-Clarke Male on-path Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpS_ICM!, !FT_MIN_ICM!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FTIML{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

            if icf == "icf":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpS_ICF!, !TF_MIN_ICF!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TFIFL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock)
                    arcpy.AddMessage("Calculating Irmischer-Clarke Female on-path Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpS_ICF!, !FT_MIN_ICF!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FTIFL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

            if three5 == "35":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpS35k!, !TF_MIN_35k!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TF35L{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                    arcpy.AddMessage("Calculating Tobler 3.5 kmh max adjustment Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpS35k!, !FT_MIN_35k!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FT35L{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

            if ur == "ur":
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctTF!, !TF_MpSUrb!, !TF_MIN_Urb!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "TFUrL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                    arcpy.AddMessage("Calculating  Tobler Urban Adjustment Calories with load weight {0}kg".format(loadlabel))
                
                for nload, loadlabel in zip(veslist, vessel_label):
                    expression = "calcSlope(!SlopePctFT!, !FT_MpSUrb!, !FT_MIN_Urb!, {0}, {1} )".format(body_mass, nload)
                    codeblock = """def calcSlope(slope, time, minutes, bmass, load):
                        if slope <= 0:
                            return ((((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time * slope))))-(((( slope ) * (bmass + load) * ( time )) / 3.5 ) - (((bmass + load) * (( slope+ 6)**2) ) / 65) + (25 * ( time**2))))* 0.014330754)*minutes           
                        else:
                            return (((1.5*bmass)+( 2.0*(bmass+load) * ( ( load/bmass) **2 ) ) + (1*(bmass+load) * (1.5*( time**2)+(0.35* time*slope))))* 0.014330754)*minutes"""
                    arcpy.CalculateField_management(input_fc, "FTUrL{0}_{1}".format(loadlabel, mass_label), expression, "PYTHON", codeblock) 
                pass

        # step 1 - interpolate shape
        lines_interpolate = arcpy.InterpolateShape_3d(input_surface, input_lines, 
                                                      r"in_memory\lines_interpolate", "", "1", 
                                                      "BILINEAR", "DENSIFY", "0")
        
        if flag_nosplit == True:
            # Process: Select Layer By Attribute
            lines_interpolate_lyr = arcpy.MakeFeatureLayer_management(lines_interpolate, "lines_interpolate_lyr")
            arcpy.SelectLayerByAttribute_management(lines_interpolate_lyr, "NEW_SELECTION", "NO_SPLIT = 1")
            lines_nosplit = arcpy.CopyFeatures_management(lines_interpolate_lyr, r"in_memory\lines_nosplit")
            
            # process no_split lines
            calculate_z(lines_nosplit)
            lines_nosplit_3D = arcpy.FeatureTo3DByAttribute_3d(lines_nosplit, r"in_memory\lines_nosplit_3D", "Start_Z", "End_Z")
            arcpy.AddMessage("Finished processing No Split lines...")
            
            # process lines to be split
            arcpy.SelectLayerByAttribute_management(lines_interpolate_lyr, "SWITCH_SELECTION", "")
            lines_2D = arcpy.CopyFeatures_management(lines_interpolate_lyr, r"in_memory\lines_2D")
            
            ## generate points
            arcpy.AddMessage("Generating sample points...")
            points = arcpy.GeneratePointsAlongLines_management(lines_2D, r"in_memory\points", "DISTANCE", sample_dist, "", "")
            
            ## Split Lines at Points
            arcpy.AddMessage("Splitting lines at points...")
            lines_3D = arcpy.SplitLineAtPoint_management(lines_2D, points, r"in_memory\lines_3D", search_radius)
            calculate_z(lines_3D)
            
            # append two datasets
            arcpy.Append_management(lines_nosplit_3D, lines_3D, "TEST", "", "")
            
            # calculate THF
            arcpy.AddMessage("Calculating walk times...")
            tobler_calc(lines_3D)
        
        else:
            lines_2D = arcpy.MakeFeatureLayer_management(lines_interpolate, "lines_2D")
            
            arcpy.AddMessage("Generating sample points...")
            points = arcpy.GeneratePointsAlongLines_management(lines_2D, r"in_memory\points", "DISTANCE", sample_dist, "", "")
            
            arcpy.AddMessage("Splitting lines at points...")
            lines_3D = arcpy.SplitLineAtPoint_management(lines_2D, points, r"in_memory\lines_3D", search_radius)
            calculate_z(lines_3D)
            
            # calculate THF
            arcpy.AddMessage("Calculating walk times...")
            tobler_calc(lines_3D)
        
        # Replace 3D walk time with 2D walk time for any No_Slope lines
        if flag_noslope == True:
            lines_3D_lyr = arcpy.MakeFeatureLayer_management(lines_3D, "lines_3D_lyr")
            arcpy.SelectLayerByAttribute_management(lines_3D_lyr, "NEW_SELECTION", "NO_SLOPE = 1")
            arcpy.CalculateField_management(lines_3D_lyr, "FT_MIN_3D", "!FT_MIN_2D!", "PYTHON", "")
            arcpy.CalculateField_management(lines_3D_lyr, "TF_MIN_3D", "!TF_MIN_2D!", "PYTHON", "")
        
        # export output
        arcpy.CopyFeatures_management(lines_3D, output_lines)

        # Delete in-memory table
        arcpy.Delete_management(r"in_memory\lines_3D")
        arcpy.Delete_management(r"in_memory\points")
        arcpy.Delete_management(r"in_memory\lines_interpolate")
        if flag_nosplit == True:
            arcpy.Delete_management(r"in_memory\lines_2D")
            arcpy.Delete_management(r"in_memory\lines_nosplit_3D")

        arcpy.CheckInExtension("3D")
        arcpy.CheckInExtension("Spatial")

        return
