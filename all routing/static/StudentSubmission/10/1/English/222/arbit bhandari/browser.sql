-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 29, 2025 at 05:15 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `browser`
--

-- --------------------------------------------------------

--
-- Table structure for table `question_set`
--

CREATE TABLE `question_set` (
  `question` text NOT NULL,
  `opt1` varchar(255) NOT NULL,
  `opt2` varchar(255) NOT NULL,
  `opt3` varchar(255) NOT NULL,
  `opt4` varchar(255) NOT NULL,
  `correct_ans` varchar(255) NOT NULL,
  `no` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `question_set`
--

INSERT INTO `question_set` (`question`, `opt1`, `opt2`, `opt3`, `opt4`, `correct_ans`, `no`) VALUES
('Which of the following is an example of supervised learning?', 'A) K-means Clustering', 'B) Linear Regression', 'C) Principal Component Analysis', 'D) Generative Adversarial Networks', 'B) Linear Regression', 1),
('In Natural Language Processing (NLP), what does \"stemming\" refer to?', 'A) Converting words to their synonyms', 'B) Removing stopwords from the text', 'C) Reducing words to their root form', 'D) Identifying named entities in the text', 'C) Reducing words to their root form', 2),
('Which of the following activation functions is most likely to cause the vanishing gradient problem in deep neural networks?', 'A) ReLU (Rectified Linear Unit)', 'B) Sigmoid', 'C) Tanh', 'D) Leaky ReLU', 'B) Sigmoid', 3),
('What does the \"curse of dimensionality\" refer to in machine learning?', 'A) Difficulty in visualizing high-dimensional data', 'B) Increased complexity and computational cost with more features', 'C) Decrease in model accuracy with increased data', 'D) Overfitting due to too many training samples', 'B) Increased complexity and computational cost with more features', 4),
('In reinforcement learning, what is the \"reward\"?', 'A) A penalty given for an incorrect action', 'B) A feedback signal indicating the success of an action', 'C) A function to approximate state values', 'D) A probability distribution over actions', 'B) A feedback signal indicating the success of an action', 5),
('Which of the following is a type of unsupervised learning algorithm?', 'A) Decision Tree', 'B) Support Vector Machine (SVM)', 'C) K-means', 'D) Random Forest', 'C) K-means', 6),
('What is \"dropout\" in the context of deep learning?', 'A) A technique for increasing the size of a dataset', 'B) A regularization method to prevent overfitting', 'C) A type of activation function', 'D) A type of optimizer', 'B) A regularization method to prevent overfitting', 7),
('Which of the following neural network architectures is primarily used for image recognition tasks?', 'A) Recurrent Neural Networks (RNN)', 'B) Convolutional Neural Networks (CNN)', 'C) Generative Adversarial Networks (GAN)', 'D) Autoencoders', 'B) Convolutional Neural Networks (CNN)', 8),
('Which metric is used to evaluate classification models?', 'A) Mean Squared Error (MSE)', 'B) Accuracy', 'C) R-squared', 'D) Mean Absolute Error (MAE)', 'B) Accuracy', 9),
('In AI, what does the Turing Test measure?', 'A) The computational efficiency of an algorithm', 'B) The ability of a machine to learn from data', 'C) The capability of a machine to exhibit intelligent behavior indistinguishable from a human', 'D) The speed of training a neural network', 'C) The capability of a machine to exhibit intelligent behavior indistinguishable from a human', 10);

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `examscore` int(11) NOT NULL,
  `Fscreen_left_time` varchar(255) NOT NULL,
  `tabs_desktop_change` varchar(255) NOT NULL,
  `trustscore` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  `Multi_Person_Detected` varchar(255) NOT NULL,
  `Smart_Phone_Detected` varchar(255) NOT NULL,
  `Gaze_Movement_Warns` varchar(255) NOT NULL,
  `unknow_person_detected` varchar(255) NOT NULL,
  `face_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`name`, `email`, `password`, `examscore`, `Fscreen_left_time`, `tabs_desktop_change`, `trustscore`, `type`, `Multi_Person_Detected`, `Smart_Phone_Detected`, `Gaze_Movement_Warns`, `unknow_person_detected`, `face_path`) VALUES
('miraj', 'miraj@gmail.com', 'miraj', 10, '', '', '0', 'admin', '', '', '', '0', NULL),
('Miraj Bhandari', 'mirajbhandari1@gmail.com', 'miraj', 0, '27 sec', '4 times', '54.25%', 'user', '6 times', '10 times', '22 times', '0 times', './faces/face1');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `question_set`
--
ALTER TABLE `question_set`
  ADD PRIMARY KEY (`no`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`email`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
