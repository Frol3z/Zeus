import maya.cmds as cmds
import maya.mel as mel

PLUGIN_NAME = 'WC'
GROUP_NAME = 'g_WeatherController'
CLOUD_OBJECT_NAME = 'WC::CloudContainer'

def log(message):
    print(f'[{PLUGIN_NAME}]: {message}')

class WeatherModel:
    def __init__(self):
        # Create plug-in group
        if not cmds.objExists(GROUP_NAME):
            self.group = cmds.group(empty=True, name=GROUP_NAME)
        else:
            self.group = GROUP_NAME

    def create_sky(self):
        # Skydome
        self.skydome = cmds.createNode('transform', name='WC::SkyDome')
        skydome_light = cmds.createNode('aiSkyDomeLight', name='aiSkyDomeLight', parent=self.skydome)
        log('SkyDomeLight created successfully!')

        # Add physical sky
        physical_sky = cmds.shadingNode('aiPhysicalSky', asTexture=True, name='aiPhysicalSky')

        # Edit intensity and sky tint attributes
        cmds.setAttr(f'{physical_sky}.intensity', 3.0)
        sky_tint_color = (0.32, 0.50, 0.84)
        cmds.setAttr(f'{physical_sky}.skyTint', *sky_tint_color, type='double3')

        # Binding physical sky to the skydome
        cmds.connectAttr(f'{physical_sky}.outColor', f'{skydome_light}.color', force=True)
        log('PhysicalSky connected successfully!')

        # Put the skydome inside the plugin group
        cmds.parent(self.skydome, self.group)

    def create_cloud_bank(self):

        # Add cloud bank
        self.cloud_container = cmds.createNode('transform', name=CLOUD_OBJECT_NAME)
        self.cloud_container_shape = cmds.createNode('fluidShape', name='cloudContainerShape', parent=self.cloud_container)

        # Load preset
        mel.eval(f'applyAttrPreset "{self.cloud_container_shape}" "customClouds" 1')

        log('Clouds created successfully!')

        # Put the cloud bank inside the plugin group
        cmds.parent(self.cloud_container, self.group)

    def create_rain(self):
        # Create the emitter
        self.rain_emitter = cmds.emitter(
            pos=(0, 0, 0),  # Position of the emitter
            type="volume",  # Emitter type set to "volume"
            n="WC:RainEmitter",  # Emitter name
            r=1000,  # Rate: Number of particles emitted per second
            sro=0,  # Start rotation: No initial rotation
            nuv=0,  # No UV tiling
            cye="none",  # Cycle: No cycling
            cyi=1,  # Cycle interval
            spd=1,  # Speed: Particle speed
            srn=0,  # Start rotation noise: No noise
            nsp=1,  # Noise strength: Set to 1
            tsp=0,  # Time step: No variation
            mxd=0,  # Maximum distance
            mnd=0,  # Minimum distance
            dx=1,  # Direction X: Emitter along X-axis
            dy=0,  # Direction Y: Emitter along Y-axis
            dz=0,  # Direction Z: Emitter along Z-axis
            sp=0,  # Speed: Particle emission speed
            vsh="cube",  # Volume shape set to cube
            vof=(0, 0, 0),  # Volume offset
            vsw=360,  # Volume sweep: 360 degrees
            tsr=0.5,  # Time step rate: 0.5
            afc=1,  # Angular factor for rotation
            afx=1,  # Angular factor X
            arx=0,  # Angular factor Y
            alx=0,  # Angular factor Z
            rnd=0,  # No randomness
            drs=0,  # Drag coefficient
            ssz=0  # Size of particles set to 0 (default)
        )

        # Scale emitter
        cmds.setAttr(f'{self.rain_emitter[0]}.scaleX', 10)
        cmds.setAttr(f'{self.rain_emitter[0]}.scaleY', 0.5)
        cmds.setAttr(f'{self.rain_emitter[0]}.scaleZ', 10)
        cmds.setAttr(f'{self.rain_emitter[0]}.rate', 0)

        # Create nParticles (and nucleus solver)
        self.rain_particles = cmds.nParticle(name='WC:RainParticles')
        cmds.connectDynamic(self.rain_particles, em=self.rain_emitter)

        # Get the shape node of the nParticle
        self.rain_particles_shape = cmds.listRelatives(self.rain_particles, shapes=True)[0]

        # Disable rain by default
        cmds.setAttr(f'{self.rain_particles_shape}.lifespanMode', 1)  # 1 is for constant lifespan mode
        cmds.setAttr(f'{self.rain_particles_shape}.lifespan', 1.5)

        # Create and assign rain material
        rain_material = cmds.shadingNode('aiStandardSurface', asShader=True, name='m_Rain')
        cmds.select(self.rain_particles)
        cmds.hyperShade(assign=rain_material)

        log('Rain emitter and nParticles created successfully!')

        # Put the rain stuff inside the plugin group
        cmds.parent(self.rain_emitter, self.group)
        cmds.parent(self.rain_particles, self.group)


    def set_cloud_density(self, value):
        normalized_value = value / 100
        # Changing opacityInputBias between 0 and 0.6
        cmds.setAttr(f'{self.cloud_container_shape}.opacityInputBias', normalized_value * 0.6)

    def set_storminess(self, is_toggled):
        if is_toggled:
            cmds.setAttr(f'{self.cloud_container_shape}.edgeDropoff', 0.5)
        else:
            cmds.setAttr(f'{self.cloud_container_shape}.edgeDropoff', 0.372)

    def set_details_amount(self, value):
        normalized_value = value / 100
        cmds.setAttr(f'{self.cloud_container_shape}.frequencyRatio', normalized_value * 3.9 + 0.1)

    def enable_rain(self, is_enabled):
        if is_enabled:
            cmds.setAttr(f'{self.rain_emitter[0]}.rate', 1000)
        else:
            cmds.setAttr(f'{self.rain_emitter[0]}.rate', 0)