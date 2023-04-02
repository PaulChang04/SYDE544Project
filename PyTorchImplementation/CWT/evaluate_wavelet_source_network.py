import numpy as np
import Wavelet_CNN_Source_Network
from torch.utils.data import TensorDataset
import torch.nn as nn
import torch.optim as optim
import torch
from torch.autograd import Variable
import time
from scipy.stats import mode
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, confusion_matrix, classification_report
import torch.nn.functional as f
import load_evaluation_dataset
import pickle

def confusion_matrix(pred, Y, number_class=7):
    confusion_matrice = []
    for x in range(0, number_class):
        vector = []
        for y in range(0, number_class):
            vector.append(0)
        confusion_matrice.append(vector)
    for prediction, real_value in zip(pred, Y):
        prediction = int(prediction)
        real_value = int(real_value)
        confusion_matrice[prediction][real_value] += 1
    return np.array(confusion_matrice)


def scramble(examples, labels, second_labels=[]):
    random_vec = np.arange(len(labels))
    np.random.shuffle(random_vec)
    new_labels = []
    new_examples = []
    if len(second_labels) == len(labels):
        new_second_labels = []
        for i in random_vec:
            new_labels.append(labels[i])
            new_examples.append(examples[i])
            new_second_labels.append(second_labels[i])
        return new_examples, new_labels, new_second_labels
    else:
        for i in random_vec:
            new_labels.append(labels[i])
            new_examples.append(examples[i])
        return new_examples, new_labels


def calculate_fitness(examples_training, labels_training, examples_test_0, labels_test_0, examples_test_1,
                      labels_test_1):
    # accuracy_test0 = []
    # accuracy_test1 = []
    accuracy_0 = []
    accuracy_1 = []
    balanced_accuracy_0 = []
    balanced_accuracy_1 = []
    f1_macro_test_0 = []
    f1_macro_test_1 = []
    conf_matrix_0 = []
    conf_matrix_1 = []
    report_0 = []
    report_1 = []

    # initialized_weights = np.load("initialized_weights.npy")
    for dataset_index in range(0, 17):
    #for dataset_index in [11, 15]:
        X_fine_tune_train, Y_fine_tune_train = [], []
        for label_index in range(len(labels_training)):
            if label_index == dataset_index:
                print("Current dataset test : ", dataset_index)
                for example_index in range(len(examples_training[label_index])):
                    if (example_index < 28):
                        X_fine_tune_train.extend(examples_training[label_index][example_index])
                        Y_fine_tune_train.extend(labels_training[label_index][example_index])
        X_test_0, Y_test_0 = [], []
        for label_index in range(len(labels_test_0)):
            if label_index == dataset_index:
                for example_index in range(len(examples_test_0[label_index])):
                    X_test_0.extend(examples_test_0[label_index][example_index])
                    Y_test_0.extend(labels_test_0[label_index][example_index])

        X_test_1, Y_test_1 = [], []
        for label_index in range(len(labels_test_1)):
            if label_index == dataset_index:
                for example_index in range(len(examples_test_1[label_index])):
                    X_test_1.extend(examples_test_1[label_index][example_index])
                    Y_test_1.extend(labels_test_1[label_index][example_index])

        X_fine_tune, Y_fine_tune = scramble(X_fine_tune_train, Y_fine_tune_train)
        valid_examples = X_fine_tune[0:int(len(X_fine_tune) * 0.1)]
        labels_valid = Y_fine_tune[0:int(len(Y_fine_tune) * 0.1)]

        X_fine_tune = X_fine_tune[int(len(X_fine_tune) * 0.1):]
        Y_fine_tune = Y_fine_tune[int(len(Y_fine_tune) * 0.1):]

        print(torch.from_numpy(np.array(Y_fine_tune, dtype=np.int32)).size(0))
        print(np.shape(np.array(X_fine_tune, dtype=np.float32)))
        train = TensorDataset(torch.from_numpy(np.array(X_fine_tune, dtype=np.float32)),
                              torch.from_numpy(np.array(Y_fine_tune, dtype=np.int32)))
        validation = TensorDataset(torch.from_numpy(np.array(valid_examples, dtype=np.float32)),
                                   torch.from_numpy(np.array(labels_valid, dtype=np.int32)))

        trainloader = torch.utils.data.DataLoader(train, batch_size=128, shuffle=True)
        validationloader = torch.utils.data.DataLoader(validation, batch_size=128, shuffle=True)

        test_0 = TensorDataset(torch.from_numpy(np.array(X_test_0, dtype=np.float32)),
                               torch.from_numpy(np.array(Y_test_0, dtype=np.int32)))
        test_1 = TensorDataset(torch.from_numpy(np.array(X_test_1, dtype=np.float32)),
                               torch.from_numpy(np.array(Y_test_1, dtype=np.int32)))

        test_0_loader = torch.utils.data.DataLoader(test_0, batch_size=1, shuffle=False)
        test_1_loader = torch.utils.data.DataLoader(test_1, batch_size=1, shuffle=False)

        cnn = Wavelet_CNN_Source_Network.Net(number_of_class=7, batch_size=128, number_of_channel=12,
                                             learning_rate=0.0404709, dropout=.5)

        criterion = nn.NLLLoss(size_average=False)
        optimizer = optim.Adam(cnn.parameters(), lr=0.0404709)

        precision = 1e-8
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer=optimizer, mode='min', factor=.2, patience=5,
                                                         verbose=True, eps=precision)

        cnn = train_model(cnn, criterion, optimizer, scheduler,
                          dataloaders={"train": trainloader, "val": validationloader}, precision=precision)

        cnn.eval()
        total = 0
        correct_prediction_test_0 = 0
        # Create empty arrays to store predicted and ground truth labels
        all_predicted_labels_0 = []
        all_ground_truth_labels_0 = []
        for k, data_test_0 in enumerate(test_0_loader, 0):
            # get the inputs
            inputs_test_0, ground_truth_test_0 = data_test_0
            inputs_test_0, ground_truth_test_0 = Variable(inputs_test_0), Variable(ground_truth_test_0)

            concat_input = inputs_test_0
            for i in range(20):
                concat_input = torch.cat([concat_input, inputs_test_0])
            outputs_test_0 = cnn(concat_input)
            _, predicted = torch.max(outputs_test_0.data, 1)
            correct_prediction_test_0 += (mode(predicted.cpu().numpy())[0][0] ==
                                          ground_truth_test_0.data.cpu().numpy()).sum()

            # Append predicted and ground truth labels to the arrays
            all_predicted_labels_0.append(mode(predicted.cpu().numpy())[0][0])
            all_ground_truth_labels_0.append(ground_truth_test_0.data.cpu().numpy())

            total += ground_truth_test_0.size(0)

        # Convert the arrays to NumPy arrays
        all_predicted_labels_0 = np.array(all_predicted_labels_0)
        all_ground_truth_labels_0 = np.concatenate(all_ground_truth_labels_0)

        # Calculate the metrics
        accuracy_0.append(accuracy_score(all_ground_truth_labels_0, all_predicted_labels_0))
        balanced_accuracy_0.append(balanced_accuracy_score(all_ground_truth_labels_0, all_predicted_labels_0))
        f1_macro_test_0.append(f1_score(all_ground_truth_labels_0, all_predicted_labels_0, average='macro'))
        conf_matrix_0.append(confusion_matrix(all_ground_truth_labels_0, all_predicted_labels_0))
        report_0.append(classification_report(all_ground_truth_labels_0, all_predicted_labels_0))

        print("ACCURACY TEST_0 FINAL : %.3f %%" % (100 * float(correct_prediction_test_0) / float(total)))
        # accuracy_test0.append(100 * float(correct_prediction_test_0) / float(total))

        total = 0
        correct_prediction_test_1 = 0
        # Create empty arrays to store predicted and ground truth labels
        all_predicted_labels_1 = []
        all_ground_truth_labels_1 = []
        for k, data_test_1 in enumerate(test_1_loader, 0):
            # get the inputs
            inputs_test_1, ground_truth_test_1 = data_test_1
            inputs_test_1, ground_truth_test_1 = Variable(inputs_test_1), Variable(ground_truth_test_1)

            concat_input = inputs_test_1
            for i in range(20):
                concat_input = torch.cat([concat_input, inputs_test_1])
            outputs_test_1 = cnn(concat_input)
            _, predicted = torch.max(outputs_test_1.data, 1)
            correct_prediction_test_1 += (mode(predicted.cpu().numpy())[0][0] ==
                                          ground_truth_test_1.data.cpu().numpy()).sum()

            # Append predicted and ground truth labels to the arrays
            all_predicted_labels_1.append(mode(predicted.cpu().numpy())[0][0])
            all_ground_truth_labels_1.append(ground_truth_test_1.data.cpu().numpy())

            total += ground_truth_test_1.size(0)

        # Convert the arrays to NumPy arrays
        all_predicted_labels_1 = np.array(all_predicted_labels_1)
        all_ground_truth_labels_1 = np.concatenate(all_ground_truth_labels_1)

        # Calculate the metrics
        accuracy_1.append(accuracy_score(all_ground_truth_labels_1, all_predicted_labels_1))
        balanced_accuracy_1.append(balanced_accuracy_score(all_ground_truth_labels_1, all_predicted_labels_1))
        f1_macro_test_1.append(f1_score(all_ground_truth_labels_1, all_predicted_labels_1, average='macro'))
        conf_matrix_1.append(confusion_matrix(all_ground_truth_labels_1, all_predicted_labels_1))
        report_1.append(classification_report(all_ground_truth_labels_1, all_predicted_labels_1))
        print("ACCURACY TEST_1 FINAL : %.3f %%" % (100 * float(correct_prediction_test_1) / float(total)))
        # accuracy_test1.append(100 * float(correct_prediction_test_1) / float(total))

    print("AVERAGE ACCURACY TEST 0 %.3f" % np.array(accuracy_0).mean())
    print("AVERAGE ACCURACY TEST 1 %.3f" % np.array(accuracy_1).mean())
    return accuracy_0, accuracy_1, balanced_accuracy_0, balanced_accuracy_1, f1_macro_test_0, f1_macro_test_1, conf_matrix_0, conf_matrix_1, report_0, report_1


def train_model(cnn, criterion, optimizer, scheduler, dataloaders, num_epochs=500, precision=1e-8):
    since = time.time()

    best_loss = float('inf')

    patience = 30
    patience_increase = 10
    for epoch in range(num_epochs):
        epoch_start = time.time()
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                cnn.train(True)  # Set model to training mode
            else:
                cnn.train(False)  # Set model to evaluate mode

            running_loss = 0.
            running_corrects = 0
            total = 0

            for i, data in enumerate(dataloaders[phase], 0):
                # get the inputs
                inputs, labels = data

                inputs, labels = Variable(inputs), Variable(labels)

                # zero the parameter gradients
                optimizer.zero_grad()
                if phase == 'train':
                    cnn.train()
                    # forward
                    outputs = cnn(inputs)
                    _, predictions = torch.max(outputs.data, 1)
                    #print(outputs.shape, labels.long().shape)
                    loss = criterion(outputs, labels.long())
                    loss.backward()
                    optimizer.step()

                    #loss = loss.data[0]

                else:
                    cnn.eval()

                    accumulated_predicted = Variable(torch.zeros(len(inputs), 7))
                    loss_intermediary = 0.
                    total_sub_pass = 0
                    for repeat in range(20):
                        outputs = cnn(inputs)
                        loss = criterion(outputs, labels.long())
                        if loss_intermediary == 0.:
                            loss_intermediary = loss
                        else:
                            loss_intermediary += loss
                        _, prediction_from_this_sub_network = torch.max(outputs.data, 1)
                        accumulated_predicted[range(len(inputs)),
                                              prediction_from_this_sub_network.cpu().numpy().tolist()] += 1
                        total_sub_pass += 1
                    _, predictions = torch.max(accumulated_predicted.data, 1)
                    loss = loss_intermediary/total_sub_pass



                # statistics
                running_loss += loss
                running_corrects += torch.sum(predictions == labels.data)
                total += labels.size(0)

            epoch_loss = running_loss / total
            epoch_acc = running_corrects / total
            print('{} Loss: {:.8f} Acc: {:.8}'.format(
                phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val':
                scheduler.step(epoch_loss)
                if epoch_loss+precision < best_loss:
                    print("New best validation loss:", epoch_loss)
                    best_loss = epoch_loss
                    torch.save(cnn.state_dict(), 'best_weights_source_wavelet.pt')
                    patience = patience_increase + epoch
        print("Epoch {} of {} took {:.3f}s".format(
            epoch + 1, num_epochs, time.time() - epoch_start))
        if epoch > patience:
            break
    print()

    time_elapsed = time.time() - since

    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val loss: {:4f}'.format(best_loss))
    # load best model weights
    cnn_weights = torch.load('best_weights_source_wavelet.pt')
    cnn.load_state_dict(cnn_weights)
    cnn.eval()
    return cnn


if __name__ == '__main__':
    # Comment between here

    # examples, labels = load_evaluation_dataset.read_data('EvaluationDataset',
    #                                             type='training0')
    #
    # datasets = [examples, labels]
    # pickle.dump(datasets, open("saved_dataset_training.p", "wb"))
    #
    # examples, labels = load_evaluation_dataset.read_data('EvaluationDataset',
    #                                             type='Test0')
    #
    # datasets = [examples, labels]
    # pickle.dump(datasets, open("saved_dataset_test0.p", "wb"))
    #
    # examples, labels = load_evaluation_dataset.read_data('EvaluationDataset',
    #                                             type='Test1')
    #
    # datasets = [examples, labels]
    # pickle.dump(datasets, open("saved_dataset_test1.p", "wb"))

    # and here if the evaluation dataset was already processed and saved with "load_evaluation_dataset"
    import os

    print(os.listdir("../"))

    datasets_training = np.load("/content/drive/MyDrive/BME544Project/saved_dataset_training.p", encoding="bytes", allow_pickle=True)
    examples_training, labels_training = datasets_training

    datasets_validation0 = np.load("/content/drive/MyDrive/BME544Project/saved_dataset_test0.p", encoding="bytes", allow_pickle=True)
    examples_validation0, labels_validation0 = datasets_validation0

    datasets_validation1 = np.load("/content/drive/MyDrive/BME544Project/saved_dataset_test1.p", encoding="bytes", allow_pickle=True)
    examples_validation1, labels_validation1 = datasets_validation1
    # print("SHAPE", np.shape(examples_training))

    accuracy_one_by_one = []
    array_training_error = []
    array_validation_error = []

    # test_0 = []
    # test_1 = []

    acc_0 = []
    acc_1 = []
    bal_0 = []
    bal_1 = []
    f1_0 = []
    f1_1 = []
    cm_0 = []
    cm_1 = []
    report_0 = []
    report_1 = []

    for i in range(3):
        print("ROUND: ", i)
        accuracy_0, accuracy_1, balanced_accuracy_0, balanced_accuracy_1, f1_macro_0, f1_macro_1, conf_matrix_0, conf_matrix_1, report_0, report_1 = calculate_fitness(examples_training, labels_training,
                                                               examples_validation0, labels_validation0,
                                                               examples_validation1, labels_validation1)
        print(accuracy_0)

        # print("TEST 0 SO FAR: ", test_0, "ACCURACY FINAL TEST 0: ", np.mean(test_0))
        # print("TEST 1 SO FAR: ", test_1, "ACCURACY FINAL TEST 1: ", np.mean(test_1))
        # print("CURRENT AVERAGE : ", (np.mean(test_0) + np.mean(test_1)) / 2.)
        acc_0.append(accuracy_0)
        acc_1.append(accuracy_1)
        bal_0.append(balanced_accuracy_0)
        bal_1.append(balanced_accuracy_1)
        f1_0.append(f1_macro_0)
        f1_1.append(f1_macro_1)
        cm_0.append(conf_matrix_0)
        cm_1.append(conf_matrix_1)

    result_name = "cnn_source_results_3.txt"

    with open(result_name, "a") as myfile:
        myfile.write("CNN STFT: \n\n")
        myfile.write("Accuracy 0: \n")
        myfile.write(str(np.mean(acc_0, axis=0)) + '\n')
        myfile.write(str(np.mean(acc_0)) + '\n')
        myfile.write("Balanced Accuracy Score 0: \n")
        myfile.write(str(np.mean(bal_0, axis=0)) + '\n')
        myfile.write(str(np.mean(bal_0)) + '\n')
        myfile.write("F1 Macro 0: \n")
        myfile.write(str(np.mean(f1_0, axis=0)) + '\n')
        myfile.write(str(np.mean(f1_0)) + '\n')
        myfile.write("Confusion Matrix 0: \n")
        myfile.write(str(np.mean(cm_0, axis=0)) + '\n')
        myfile.write(str(np.mean(np.mean(cm_0, axis=0))) + '\n')
        myfile.write("Classification Report 0: \n")
        myfile.write('\n'.join(str(report_0) for report in report_0))

        myfile.write("Accuracy 1: \n")
        myfile.write(str(np.mean(acc_1, axis=0)) + '\n')
        myfile.write(str(np.mean(acc_1)) + '\n')
        myfile.write("Balanced Accuracy Score 1: \n")
        myfile.write(str(np.mean(bal_1, axis=0)) + '\n')
        myfile.write(str(np.mean(bal_1)) + '\n')
        myfile.write("F1 Macro 1: \n")
        myfile.write(str(np.mean(f1_1, axis=0)) + '\n')
        myfile.write(str(np.mean(f1_1)) + '\n')
        myfile.write("Confusion Matrix 1: \n")
        myfile.write(str(np.mean(cm_1, axis=0)) + '\n')
        myfile.write(str(np.mean(np.mean(cm_1, axis=0))) + '\n')
        myfile.write("Classification Report 1: \n")
        myfile.write('\n'.join(str(report_1) for report in report_1))

        myfile.write("Average: \n")
        myfile.write(str(np.mean(acc_0) + np.mean(acc_1) / 2.))
        myfile.write("Balanced Accuracy Score: \n")
        myfile.write(str(np.mean(bal_0) + np.mean(bal_1) / 2.))
        myfile.write("F1 Macro: \n")
        myfile.write(str(np.mean(f1_0) + np.mean(f1_1) / 2.))
        myfile.write("Confusion Matrix: \n")
        myfile.write(str(np.mean([np.mean(cm_0, axis=0),np.mean(cm_1, axis=0)], axis=0)) + '\n')
        myfile.write("\n\n\n")

        for report in report_0:
            with open(result_name, "a") as myfile:
                myfile.write("Classification Report 0: \n")
                myfile.write(report)

        for report in report_1:
            with open(result_name, "a") as myfile:
                myfile.write("Classification Report 1: \n")
                myfile.write(report)
