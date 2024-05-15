import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import JointState
import time
import numpy as np
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult

"""

class pidControllerNode(Node):
    def __init__(self):
        super().__init__('PID_Node')
        self.declare_parameter('kp',0.3)#0.45)
        self.declare_parameter('ki',0.08)#0.14)
        self.declare_parameter('kd',0.14)#0.18)
        self.declare_parameter('setpoint',0.0)
        self.Kp = self.get_parameter('kp').value
        self.Ki = self.get_parameter('ki').value
        self.Kd = self.get_parameter('kd').value
        self.setpoint_x = 0
        self.setpoint_y = 0
        self.lastError = 0
        self.lastError_2 = 0 
        self.IntegralError = 0
        self.IntegralError_2 = 0
        self.DerivativeError = 0
        self.DerivativeError_2 = 0
        self.start_time = 0
        self.x_pos = 0.0
        self.y_pos = 0.0

        #Initialize pub
        self.publisher_ = self.create_publisher(
            Float32MultiArray, 
            'PID_PR', 
            10)

        self.publisher_JS = self.create_publisher(
            JointState, 
            'joint_states', 
            5)
        
        #Initialize sub
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'ball_dist_cm',
            self.sub_callback,
            10)
        self.add_on_set_parameters_callback(self.parameter_callback)
        self.joint_state = JointState()
        
        
        
    def sub_callback(self, msg):
        self.x_pos, self.y_pos = msg.data

        self.joint_state.name =['pitch','roll','ballx','bally']
        self.joint_state.position=[0.90, 0.3, 0.10, 0.10]
        

        #self.setpoint_x =float(80 * np.cos(time.time()) / 10)#
        #self.setpoint_y =float(80 * np.sin(time.time()) / 10)#
        #self.setpoint_x = float(80 * np.sin(2*time.time())/10)
        #self.setpoint_y = float(80 * np.sin(time.time())/10)

        pid_pitch = self.compute_pitch(self.x_pos)
        pid_roll = self.compute_roll(self.y_pos)

        pid_output = pid_pitch, pid_roll
        self.get_logger().info('pid_pitch: %f' % pid_output[0])
        self.get_logger().info('pid_roll: %f' % pid_output[1])
        pub_msg = Float32MultiArray(data=pid_output)
        self.publisher_.publish(pub_msg)
        self.publisher_JS.publish(self.joint_state)


    def compute_pitch(self, systemValue):
        dt = 0.03
        error = self.setpoint_y - systemValue
        self.IntegralError += error * dt
        self.IntegralError = np.clip(self.IntegralError, a_min=-5, a_max=5)  # integral windup
        self.DerivativeError = (error - self.lastError) / dt
        self.get_logger().info('IntegralError: %f' % self.IntegralError)
        

        output = (-self.Kp * error) + (-self.Ki * self.IntegralError) + (-self.Kd * self.DerivativeError)
    
        self.lastError = error
        return output


    def compute_roll(self, systemValue):
        dt = 0.03
        error = self.setpoint_x - systemValue
        self.IntegralError_2 += error * dt
        self.IntegralError_2 = np.clip(self.IntegralError_2, a_min=-5, a_max=5)  # integral windup
        self.DerivativeError_2 = (error - self.lastError_2) / dt
        self.get_logger().info('IntegralError_2: %f' % self.IntegralError_2)

        output = (-self.Kp * error) + (-self.Ki * self.IntegralError_2) + (-self.Kd * self.DerivativeError_2)

        self.lastError_2 = error

        return output
    
    def parameter_callback(self, params:list[Parameter]):
        for param in params:
            if param.name == 'kp':
                self.Kp = param.value
            if param.name == 'ki':
                self.Ki = param.value
            if param.name == 'kd':
                self.Kd = param.value

    
        return SetParametersResult(successful=True)


def main(args=None):
    rclpy.init(args=None)
    pidControllerNode_ = pidControllerNode()

    rclpy.spin(pidControllerNode_)
    pidControllerNode_.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

"""

    

class pidControllerNode(Node):
    def __init__(self):
        super().__init__('PID_Node')
        self.load_parameters()
        
        self.state = {
            'x': {'pos': 0.0, 'setpoint': 0, 'lastError': 0, 'integralError': 0, 'derivativeError': 0},
            'y': {'pos': 0.0, 'setpoint': 0, 'lastError': 0, 'integralError': 0, 'derivativeError': 0}
        }

        self.init_publishers()
        self.init_subscribers()
        self.joint_state = JointState(names=['pitch', 'roll', 'ballx', 'bally'], positions=[0.90, 0.3, 0.10, 0.10])
        
    def load_parameters(self):
        self.declare_parameters(
            namespace='',
            parameters=[
                ('kp', 0.3),
                ('ki', 0.08),
                ('kd', 0.14),
                ('setpoint_x', 0.0),
                ('setpoint_y', 0.0)
            ]
        )
        self.Kp = self.get_parameter('kp').value
        self.Ki = self.get_parameter('ki').value
        self.Kd = self.get_parameter('kd').value

    def init_publishers(self):
        self.publisher_ = self.create_publisher(Float32MultiArray, 'PID_PR', 10)
        self.publisher_JS = self.create_publisher(JointState, 'joint_states', 5)

    def init_subscribers(self):
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'ball_dist_cm',
            self.sub_callback,
            10
        )

    def sub_callback(self, msg):
        self.state['x']['pos'], self.state['y']['pos'] = msg.data
        pid_outputs = {}

        for axis in ['x', 'y']:
            pid_outputs[axis], self.state[axis]['lastError'], self.state[axis]['integralError'], self.state[axis]['derivativeError'] = \
                self.compute_control(self.state[axis]['pos'], self.get_parameter(f'setpoint_{axis}').value, **self.state[axis])

        self.get_logger().info(f'pid_pitch: {pid_outputs["x"]:.2f}, pid_roll: {pid_outputs["y"]:.2f}')
        pub_msg = Float32MultiArray(data=[pid_outputs['x'], pid_outputs['y']])
        self.publisher_.publish(pub_msg)
        self.publisher_JS.publish(self.joint_state)

    def compute_control(self, systemValue, setpoint, lastError, integralError, derivativeError, dt=0.03):
        error = setpoint - systemValue
        integralError += error * dt
        integralError = np.clip(integralError, a_min=-5, a_max=5)
        derivativeError = (error - lastError) / dt
        output = (-self.Kp * error) + (-self.Ki * integralError) + (-self.Kd * derivativeError)
        return output, error, integralError, derivativeError

    def parameter_callback(self, params:list[Parameter]):
        for param in params:
            setattr(self, param.name, param.value)
        return SetParametersResult(successful=True)

def main(args=None):
    rclpy.init(args=args)
    node = pidControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
