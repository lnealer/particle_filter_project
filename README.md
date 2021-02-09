# particle_filter_project

### Robotics Project 2 Implementation
Team Members: Kenneth Humphries, Leandra Nealer

A 1-2 sentence description of how your team plans to implement each of the following components of the particle filter as well as a 1-2 sentence description of how you will test each component:

### How you will initialize your particle cloud (initialize_particle_cloud()).
The particle cloud will be initialized as a list of points. These points will either be randomly generated, or evenly distributed across the map.

### How you will update the position of the particles will be updated based on the movements of the robot (update_particles_with_motion_model()).
Each particle will store the position and rotation (x,y, z_rot).  The values of each particle will be changed based on the difference between the current and previous odometer values.

### How you will compute the importance weights of each particle after receiving the robot's laser scan data (update_particle_weights_with_measurement_model())
We will retrieve data from the LaserScan at positions 0, 90, 180, and 270 degrees. We’ll mathematically compute the distance to each wall from each particle. We will compute each weight by following the formula for MonteCarlo Localization provided in Class Meeting 5.

### How you will normalize the particles' importance weights (normalize_particles()) and resample the particles (resample_particles()).
These two methods will again follow the MonteCarlo Localization process. For resampling, we will select our sample based proportionally on each points’ importance value.

### How you will update the estimated pose of the robot (update_estimated_robot_pose())
This method will physically move the robot a set distance or rotation, and return the updated odometer values.

### How you will incorporate noise into your particle filter.
We will update the robots positions at small increments so as to minimize drift and noise. Then, as we know the noise will be bounded by a small number, we’ll randomly ‘nudge’ each particle by a small value.

### A brief timeline sketching out when you would like to have accomplished each of the components listed above.
Here is our ideal order of implementation:
* initialize_particle_cloud()
* update_particles_with_motion_model()
* update_estimated_robot_pose()
* update_particle_weights_with_measurement_model()
* normalize_particles()
* resample_particles()
* Accounting for noise


--------------------


# Particle Filter Project Writeup

## Objectives Description
The purpose of this project was localize the position of our turtlebot on a given map by utilizing a particle filter algorithm. Specifically, this project's primary goal was to determine the position of a robot provided only a map and the sensory data of the robot itself.
## High Level Description
To achieve this goal, we elected to use a Monte-Carlo simulation over many, randomly placed points to produce a weighted estimate on the robot's position. Once the "particle cloud" of random points on the map is initialized. Our program waits for a sufficient change in the turtlebot's odometry. Upon recognizing such a change in the robot's position or orientation, the algorithm attempts to update the position of every point in the cloud (with some randomness to account for noise), as well as adjust their weight values to determine the accuracy of each guess. To do so, the algorithm accepts a series of range values from the robot's Lidar scanner. Then, each of these ranges are applied to every point in the cloud, and a likelihood field is used to determine how far these new points are from the nearest obstacle (a closest distance of 0 would imply a minimum error for this point.) Finally, the weights of every point are normalized, and the process is repeated for a new sample of points determined by the weights.
## Step 1: Movement
Movement of the robot was primarily performed by the provided turtlebot3_teleop_key launch file. Whenever the robot was moved, the pose returned by the geometry was updated in robot_scan_received() and the change in position/orientation was applied to every point in update_particles_with_motion_model(). The estimated pose of the robot was a weighted average of these points, calculated within  update_estimated_robot_pose().
### Code Description:
**robot_scan_received():** This method runs every time a LaserScan message is recieved by the code. Using the robot's odometry, it updates the current and previous positions of the robot based on sensory data. If the robot has moved a sufficient distance, the rest of the particle filter algorithm (including those mentioned in this section) are run from this function.
**update_particles_with_motion_model():** Using the current and previous poses returned by the odometry, this method calculates a the robot's change in x, y, and theta (yaw.) These values, in addition to a random noise factor, are applied to every point in the cloud.
**update_estimated_robot_pose():** This method takes the weighted average of every point in the cloud's x, y, and theta values. The estimated robot pose is simply a point placed at these average values.
## Step 2: Computation of Importance Weights
Within the initialization of the particle filter, the particles themselves are created randomly via the initialize_particle_cloud() method. When the weights of these particles need to be recalculated, update_particle_weights_with_measurement_model() is called from the previously discussed robot_scan_recieved(). These new weights must also be normalized via normalize_particles() before they can be used.
### Code Description:
**initialize_particle_cloud():** In true Monte-Carlo fashion, this method creates a random assortment of 2500 particles across the entire map. Their initial weights are set to 1, which are then normalized to 1/2500 later in the code.
**update_particle_weights_with_measurement_model():** This code utilizes the "likelihood_field.py" file provided during lesson 6 of this class (as well as a helper-function from measurement_update_likelihood_field.py.) It applies a transformation based on the robot's lidar data to every point in the cloud and then finds the closest obstacle to these new points by invoking the likelihood_field class' "get_closest_obstacle_distance()" method. Finally, these distance values are applied to a zero-centered gaussian distribution (provided from lesson 6) to determine the original point's error, and calculates a new weight for each of these points based on said error values.
**normalize_particles():** This method simply calculates the sum of every particle's weight, and divides each weight by the sum.
## Step 3: Resampling
As the new weights and positions of every particle in the cloud has already been calculated, all that is left to do is select a new set of points for the next set of calculations! This goal is achieved within the resample_particles() method.
### Code Description
** resample_particle(): ** Provided within the starter code is a method "draw_random_sample()" which takes a list of values along with their corresponding probability values to create a new, randomly selected sample that reflects these probabilities. resample_particle() invokes this method with the particle cloud as the original sample, and a list of their weights as the probabilities. The returned list is set as the new particle cloud.

------------

*To summarize the general workflow of the algorithm:*
Within the particle filter's initialization:

- initialize_particle_cloud()

Continuously call:
- robot_scan_received()

If the robot has moved far enough:
- update_particles_with_motion_model()
- update_particle_weights_with_measurement_model() # This includes consideration for noise.
- normalize_particles()
- resample_particles()
- normalize_particles() # To ensure the sum of the wieghts is 1 for the estimated robot pose calculation.
- update_estimated_robot_pose()

## Challenges
We faced a multitude of challenges while implementing the particle filter for our project. The first of these challenges was the initialization of the particle cloud on the map. Initially, many of our initial points would be generated outside the map, or the particle cloud as a whole would not properly overlay the map upon being published. To solve this problem, We had to rescale the particles based upon the resolution of the map in RVIZ so that they were properly displayed. In addition to this, we had to reject random particles that were not contained by boundaries of the map and create a new one. These changes allowed the random particles to properly fill the entirety of the map's house and nothing more.
Another problem faced during the creation of the particle filter was the calculation of the estimated robot pose. Oftentimes, the estimated robot pose would not seem to properly reflect the weighted average of the particles, both in terms of position and orientation. To solve this problem, we had to ensure that the resampled particles were normalized before the update_estimated_robot_pose() method was called. Furthermore,  some special trigonometry was required to account for the circular nature of the yaw values (simply summing every yaw value was not sufficient.) Overall, these changes allowed a proper weighted average calculation for the estimated robot pose.
One final problem we faced was the convergence of the particle cloud on incorrect locations over time. The possibility of this occurring was minimized by increasing the number of particles, increasing the standard deviation of the gaussian distribution (a low s.d. meant that the points converged too quickly), and increasing the number of range values taken from the Lidar from 4 to 12 to 36. However, the calculation time required for a significant amount of points was noticeably high, and would cause errors if the robot attempted a new calculation before the previous was complete. Therefore, a balance between accuracy and performance had to be met.
## Future Work
As mentioned in the previous paragraph, the accuracy of our program was bottlenecked by the performance of the particle cloud calculations. As it is difficult to optimize performance in python, future improvements in our project would need to handle cases where the particle cloud converges on the wrong spot. For instance, a new method could be created by the name of "check_accuracy_of_particle_cloud()." This method would check the sum of the particles' weights to determine if there is a significant, systematic error across the entirety of the cloud. If so, the particle cloud itself would be reinitialized, and the process would begin from scratch. Ultimately, this check for false positives in the particle cloud would allow the algorithm to consider cases where it needs to reevaluate its estimated robot position.
## Key Takeaways
- This project has demonstrated to us that there is never a "correct" solution to many of the problems faced in robotics. For instance, our calculation of particle weights via a likelihood field is by no means to only way to determine the accuracy of our particles. Rather, there are many solutions to any problem, each with their own benefits and detrements.
-  Furthermore, we have learned from this project that a daunting task in robotics can be overcome by the breaking down of the issue into finite steps. As seen earlier in this writeup, the heart of our algorithm is divided into a series of relatively small functions that each complete a single step in the particle filter process. By programming these methods one at a time, we were able to complete this project with a minimal amount of stress or conflict.

## Gif of Behavior:
![particle_filter.gif](particle_filter.gif)
