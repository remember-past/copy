import datetime
import copy
def predict_vm(ecs_lines, input_lines):
    # Do your work from here#
    result = []
    if ecs_lines is None:
        print 'ecs information is none'
        return result
    if input_lines is None:
        print 'input file information is none'
        return result
    # process inputfile and get useful information

    # physical server information
    input_lines_0=input_lines[0].strip('\r\n').strip('\n').split(' ')
    physical_server_cpu_kernel = int(input_lines_0[0])
    physical_server_memory_size = int(input_lines_0[1])
    physical_server_desk_kernel = int(input_lines_0[2])

    # virtual machine information
    input_lines_2=input_lines[2].strip('\r\n').strip('\n')
    virtual_machine_model_number_count = int(input_lines_2)
    virtual_name_prefix='flavor'
    #[(integer)model number,cpu kernel,memory size,(string)model number]
    virtual_machine_list=[]
    for i in range(3,3+virtual_machine_model_number_count):
        temp=input_lines[i].strip('\r\n').strip('\n').split(' ')
        virtual_machine_each=[]
        virtual_machine_each.append(int(temp[0].strip(virtual_name_prefix)))
        virtual_machine_each.append(int(temp[1]))
        virtual_machine_each.append(int(temp[2])/1024)
        virtual_machine_each.append(temp[0])
        virtual_machine_list.append(virtual_machine_each)

    #packing optimization target CPU or MEM
    optimization_target = input_lines[4+virtual_machine_model_number_count].strip('\r\n').strip('\n')

    #prediction time
    prediction_start_time = input_lines[6+virtual_machine_model_number_count].strip('\r\n').strip('\n')
    prediction_end_time = input_lines[7+virtual_machine_model_number_count].strip('\r\n').strip('\n')

    formal_p_strat_time = datetime.datetime.strptime(prediction_start_time, '%Y-%m-%d %H:%M:%S')
    formal_p_end_time = datetime.datetime.strptime(prediction_end_time, '%Y-%m-%d %H:%M:%S')
    prediction_day = (formal_p_end_time-formal_p_strat_time).days

    # process train data and get average result
    # train data format
    # [(integer)machine model number,(str)time]

    train_data_list=[]
    virtual_machine_model_number_total_count = 15
    # virtual machine number for every model
    virtual_machine_every_number=[0]*virtual_machine_model_number_total_count


    for i in ecs_lines:
        temp = i.strip('\r\n').strip('\n').split('\t')
        train_data_each=[]
        train_data_each.append(int(temp[1].strip(virtual_name_prefix)))
        train_data_each.append(temp[2])
        if(train_data_each[0]<=15):
            virtual_machine_every_number[train_data_each[0] - 1] = virtual_machine_every_number[train_data_each[0] - 1] + 1
        train_data_list.append(train_data_each)
    train_start_time=datetime.datetime.strptime(train_data_list[0][1], '%Y-%m-%d %H:%M:%S')
    train_end_time=datetime.datetime.strptime(train_data_list[-1][1], '%Y-%m-%d %H:%M:%S')

    train_day=(train_end_time-train_start_time).days

    # using average number giving prediction number
    # prdiction number list corresponding to virtual machine list
    prediction_number_list=[]
    for i in virtual_machine_list:
        temp=virtual_machine_every_number[i[0]-1]*prediction_day/train_day
        prediction_number_list.append(temp)
    test_data_list=[0,13,3,0,2]

    # bin packing step
    # flavor status
    #[model,cpu kernel,mem size,prediction number]
    #bin,[cpu kernel,mem size,[model,model,...]]
    prediction_virtual_machine_list=[]
    for i in range(len(virtual_machine_list)):
        temp=[]
        temp.append(virtual_machine_list[i][0])
        temp.append(virtual_machine_list[i][1])
        temp.append(virtual_machine_list[i][2])
        #temp.append(test_data_list[i])
        temp.append(prediction_number_list[i])
        prediction_virtual_machine_list.append(temp)
    bins=bin_packing_fisrt_fit(prediction_virtual_machine_list,physical_server_cpu_kernel,physical_server_memory_size,optimization_target)

    #process result file
    prediction_virtual_machine_total_number=sum(prediction_number_list)
    result.append(prediction_virtual_machine_total_number)
    for i in prediction_virtual_machine_list:
        str="%s%d %d"%(virtual_name_prefix,i[0],i[3])
        result.append(str)
    result.append('')
    result.append(len(bins))
    for i in range(len(bins)):
        temp=bins[i][2]
        str="%d"%(i+1)
        dic={}
        for j in temp:
            dic[j]=dic.setdefault(j,0)
            dic[j]=dic[j]+1
        for key in dic:
            str=str+" %s%d %d"%(virtual_name_prefix,key,dic[key])
        result.append(str)
    return result

def bin_packing_fisrt_fit(prediction_virtual_machine_list,physical_server_cpu_kernel,physical_server_memory_size,optimization_target):
    #start
    bins=[]
    prediction_virtual_machine_list_copy=copy.deepcopy(prediction_virtual_machine_list)
    if(optimization_target=='CPU'):
        target=1
    else:
        target=2
    sorted_prediction_virtual_machine_list=sorted(prediction_virtual_machine_list_copy, key=lambda vm_list: vm_list[target],reverse=True)

    #initialization bin
    temp_bin=[physical_server_cpu_kernel,physical_server_memory_size]
    temp_model=[]
    temp_bin.append(temp_model)
    bins.append(temp_bin)
    #pointer point to the place of packing
    #if pointer >= length of  prediction_virtual_machine_list,break
    pointer=0
    while(pointer< len(prediction_virtual_machine_list)):
        if(sorted_prediction_virtual_machine_list[pointer][3]>0):
            #packing
            sorted_prediction_virtual_machine_list[pointer][3]=sorted_prediction_virtual_machine_list[pointer][3]-1
            cpu_kernel=sorted_prediction_virtual_machine_list[pointer][1]
            mem_size=sorted_prediction_virtual_machine_list[pointer][2]
            id=sorted_prediction_virtual_machine_list[pointer][0]

            packed=False
            for each_bin in bins:
                if(each_bin[0]>=cpu_kernel and each_bin[1]>=mem_size):
                    each_bin[0]=each_bin[0]-cpu_kernel
                    each_bin[1]=each_bin[1]-mem_size
                    each_bin[2].append(id)
                    packed=True
                    break
            if(not packed):
                temp_bin = [physical_server_cpu_kernel, physical_server_memory_size]
                temp_model = []
                temp_bin.append(temp_model)
                bins.append(temp_bin)
                bins[-1][0] = bins[-1][0] - cpu_kernel
                bins[-1][1] = bins[-1][1] - mem_size
                bins[-1][2].append(id)
                packed = True
            #print "pointer %d"%(pointer)
        else:
            pointer = pointer + 1
    return bins