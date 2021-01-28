# particle_filter_project

###Robotics Project 2 Implementation
Team Members: Kenneth Humphries, Leandra Nealer

A 1-2 sentence description of how your team plans to implement each of the following components of the particle filter as well as a 1-2 sentence description of how you will test each component:

###How you will initialize your particle cloud (initialize_particle_cloud()).
The particle cloud will be initialized as a list of points. These points will either be randomly generated, or evenly distributed across the map.

###How you will update the position of the particles will be updated based on the movements of the robot (update_particles_with_motion_model()).
Each particle will store the position and rotation (x,y, z_rot).  The values of each particle will be changed based on the difference between the current and previous odometer values.

###How you will compute the importance weights of each particle after receiving the robot's laser scan data (update_particle_weights_with_measurement_model())
We will retrieve data from the LaserScan at positions 0, 90, 180, and 270 degrees. We’ll mathematically compute the distance to each wall from each particle. We will compute each weight by following the formula for MonteCarlo Localization provided in Class Meeting 5.

###How you will normalize the particles' importance weights (normalize_particles()) and resample the particles (resample_particles()).
These two methods will again follow the MonteCarlo Localization process. For resampling, we will select our sample based proportionally on each points’ importance value.

###How you will update the estimated pose of the robot (update_estimated_robot_pose())
This method will physically move the robot a set distance or rotation, and return the updated odometer values.

###How you will incorporate noise into your particle filter.
We will update the robots positions at small increments so as to minimize drift and noise. Then, as we know the noise will be bounded by a small number, we’ll randomly ‘nudge’ each particle by a small value.

###A brief timeline sketching out when you would like to have accomplished each of the components listed above.
Here is our ideal order of implementation:
*initialize_particle_cloud()
*update_particles_with_motion_model()
*update_estimated_robot_pose()
*update_particle_weights_with_measurement_model()
*normalize_particles()
*resample_particles()
*Accounting for noise

