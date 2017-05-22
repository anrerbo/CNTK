import cntk as C
from cntk.io import MinibatchSource, HTKFeatureDeserializer, HTKMLFDeserializer, StreamDef, StreamDefs
from cntk.layers import Recurrence, Dense, LSTM, Sequential, For

import os
abs_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(abs_path, "..", "..", "..", "..", "Examples", "Speech", "AN4", "Data")


def test_htk_deserializers():
    mbsize = 640
    epoch_size = 1000 * mbsize
    lr = [0.001]

    feature_dim = 33
    num_classes = 132
    context = 2

    os.chdir(data_path)

    features_file = "glob_0000.scp"
    labels_file = "glob_0000.mlf"
    label_mapping_file = "state.list"

    fd = HTKFeatureDeserializer(StreamDefs(
        amazing_features = StreamDef(shape=feature_dim, context=(context,context), scp=features_file)))

    ld = HTKMLFDeserializer(label_mapping_file, StreamDefs(
        awesome_labels = StreamDef(shape=num_classes, mlf=labels_file)))

    reader = MinibatchSource([fd,ld])

    features = C.sequence.input_variable(((2*context+1)*feature_dim))
    labels = C.sequence.input_variable((num_classes))

    model = Sequential([For(range(3), lambda : Recurrence(LSTM(256))),
                        Dense(num_classes)])
    z = model(features)
    ce = C.cross_entropy_with_softmax(z, labels)
    errs = C.classification_error    (z, labels)

    learner = C.fsadagrad(z.parameters,
                          lr=C.learning_rate_schedule(lr, C.UnitType.sample, epoch_size),
                          momentum=C.momentum_schedule(0.52729),
                          gradient_clipping_threshold_per_sample=15, gradient_clipping_with_truncation=True)
    progress_printer = C.logging.ProgressPrinter(freq=0)
    trainer = C.Trainer(z, (ce, errs), learner, progress_printer)

    input_map={ features: reader.streams.amazing_features, labels: reader.streams.awesome_labels }

    # just run and verify it doesn't crash
    for i in range(3):
        mb_data = reader.next_minibatch(mbsize, input_map=input_map)
        trainer.train_minibatch(mb_data)
    assert True
    os.chdir(abs_path)

#test_htk_deserializers()
