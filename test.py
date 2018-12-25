

class Amalgalma:
    """
    Some example commemt
    """

    def test_func(self,a):
        """
        Some example comment for function.
        :param a:
        :return:
        """
        pass


class ClassB(Amalgalma):

    def test_func(self,a):
        mdict = locals() 
        del mdict['self'] 
        del mdict['__class__'] 
        super(ClassB, self).test_func(**locals())


    class TrololoClass:
        pass
